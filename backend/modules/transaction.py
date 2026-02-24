import re
from datetime import datetime
from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def __init__(self):
        self.states = {} 
        self.CRYPTO_TICKERS = ["BTC", "ETH", "BNB", "SOL", "DOT", "ADA", "XRP", "USDT", "LINK", "DOGE"]
        self.EXCHANGE_RATE_USD = 25450 # Cập nhật theo tỷ giá Portfolio

    def get_info(self):
        return {"id": "transaction", "name": "➕ Giao dịch"}

    def _get_cash_balance(self, user_id):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH'", (user_id,))
            res = cursor.fetchone()
            return res[0] if res[0] is not None else 0

    def run(self, user_id, data=None):
        if not data:
            self.states[user_id] = {} 
            return {
                "status": "wizard",
                "message": "📱 *QUẢN LÝ GIAO DỊCH*\nBạn muốn giao dịch gì?",
                "buttons": ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác", "🏠 Trang chủ", "❌ Hủy"]
            }

        text = data.strip()
        NAV_COMMANDS = ["🏠 Trang chủ", "💼 Tài sản của bạn", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác", "📜 Lịch sử", "🎯 Mục tiêu", "📈 Báo cáo", "⚙️ Cài đặt"]
        if text in NAV_COMMANDS:
            self.states[user_id] = {}
            return "EXIT_SIGNAL"

        text_clean = text.replace(",", ".")
        
        # --- BƯỚC 1: KIỂM TRA LỆNH NHANH ---
        quick_res = self._parse_quick_command(user_id, text_clean)
        if quick_res:
            self.states[user_id] = {} 
            return quick_res

        # --- BƯỚC 2: KIỂM TRA NÚT BẤM MENU CON ---
        menu_internal = ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác", "❌ Hủy", "Mua", "Bán", "Nạp", "Rút", "🏠 Trang chủ"]
        if text in menu_internal:
            if text in ["❌ Hủy", "🏠 Trang chủ"]:
                self.states[user_id] = {}
                return "🏠 Quay lại màn hình chính."
            
            if text in ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác"]:
                self.states[user_id] = {"flow": text, "step": "ask_ticker" if text != "💵 Tiền mặt" else "ask_side"}
                return self._get_wizard_question(text, self.states[user_id])

        # --- BƯỚC 3: XỬ LÝ WIZARD ---
        state = self.states.get(user_id, {})
        flow = state.get("flow")
        if flow in ["📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác"]:
            return self._handle_assets_wizard(user_id, text_clean, state)
        if flow == "💵 Tiền mặt":
            return self._handle_cash_wizard(user_id, text_clean, state)

        return "❓ Không rõ yêu cầu. Hãy chọn menu hoặc gõ lệnh nhanh (VD: nap 1ty, vcb 100 55)."

    def _get_wizard_question(self, flow, state):
        if flow == "💵 Tiền mặt":
            return {"status": "wizard", "message": "📱 *CASH FLOW*\n➡️ Bạn muốn Nạp hay Rút tiền?", "buttons": ["Nạp", "Rút", "❌ Hủy"]}
        return {"status": "wizard", "message": f"📱 *{flow}*\n➡️ Mã tài sản là gì?", "buttons": ["❌ Hủy"]}

    def _parse_quick_command(self, user_id, text):
        t = text.lower().strip()
        # Lệnh tiền mặt: nap 100tr, rut 10tr
        cash_match = re.search(r"(nạp|nap|rút|rut)\s*(\d+\.?\d*)\s*(tỷ|ty|tr|triệu|k)?", t)
        if cash_match:
            side_text = cash_match.group(1)
            val = self._parse_value(t)
            t_type = "IN" if side_text in ["nạp", "nap"] else "OUT"
            if t_type == "OUT" and self._get_cash_balance(user_id) < val: return "❌ Ôi Bạn Hết Tiền Rồi!!"
            return self._save_to_db(user_id, "CASH", t_type, "VND", 1, val if t_type == "IN" else -val)

        # Lệnh tài sản: vcb 100 55
        asset_match = re.match(r"^([a-z0-9]{2,10})\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)$", t)
        if asset_match:
            ticker = asset_match.group(1).upper()
            amount = float(asset_match.group(2))
            price = float(asset_match.group(3))
            a_type = "CRYPTO" if ticker in self.CRYPTO_TICKERS or len(ticker) > 5 else "STOCK"
            t_type = "BUY" if amount > 0 else "SELL"
            if a_type == "STOCK" and price < 1000: price *= 1000
            return self._save_to_db(user_id, a_type, t_type, ticker, abs(amount), price)
        return None

    def _handle_assets_wizard(self, user_id, text, state):
        step = state.get("step")
        a_map = {"📊 Cổ phiếu": "STOCK", "🪙 Crypto": "CRYPTO", "🥇 Đầu tư khác": "OTHER"}
        a_type = a_map.get(state["flow"], "OTHER")

        if step == "ask_ticker":
            state.update({"ticker": text.upper(), "step": "ask_side"})
            return {"status": "wizard", "message": f"Mã: {text.upper()}\n➡️ Bạn muốn Mua hay Bán?", "buttons": ["Mua", "Bán", "❌ Hủy"]}
        if step == "ask_side":
            if text not in ["Mua", "Bán"]: return "Vui lòng chọn Mua hoặc Bán."
            state.update({"side": "BUY" if text == "Mua" else "SELL", "step": "ask_amount"})
            return {"status": "wizard", "message": "➡️ Số lượng bao nhiêu?", "buttons": ["❌ Hủy"]}
        if step == "ask_amount":
            try:
                state.update({"amount": float(text.replace(",", ".")), "step": "ask_price"})
                return {"status": "wizard", "message": "➡️ Giá giao dịch?", "buttons": ["❌ Hủy"]}
            except: return "⚠️ Nhập số lượng bằng con số."
        if step == "ask_price":
            try:
                price = float(text.replace(",", "."))
                if a_type == "STOCK" and price < 1000: price *= 1000
                res = self._save_to_db(user_id, a_type, state["side"], state["ticker"], state["amount"], price)
                self.states[user_id] = {}
                return res
            except: return "⚠️ Nhập giá bằng con số."

    def _handle_cash_wizard(self, user_id, text, state):
        step = state.get("step")
        if step == "ask_side":
            if text not in ["Nạp", "Rút"]: return "Vui lòng chọn Nạp hoặc Rút."
            state.update({"side": "IN" if text == "Nạp" else "OUT", "step": "ask_value"})
            return {"status": "wizard", "message": f"➡️ Số tiền {text} bao nhiêu?", "buttons": ["❌ Hủy"]}
        if step == "ask_value":
            val = self._parse_value(text)
            if val == 0: return "⚠️ Số tiền không hợp lệ."
            if state["side"] == "OUT" and self._get_cash_balance(user_id) < val: return "❌ Ôi Bạn Hết Tiền Rồi!!"
            res = self._save_to_db(user_id, "CASH", state["side"], "VND", 1, val if state["side"] == "IN" else -val)
            self.states[user_id] = {}
            return res

    def _save_to_db(self, user_id, a_type, t_type, ticker, amount, price):
        # total_val cho Crypto tính bằng USD, Stock tính bằng VND
        total_val = amount * price
        # Quy đổi ra VND để trừ tiền mặt
        cost_vnd = abs(total_val) * (self.EXCHANGE_RATE_USD if a_type == "CRYPTO" else 1)
        
        # Kiểm tra số dư nếu là lệnh Mua (BUY)
        if a_type != "CASH" and t_type == "BUY":
            if self._get_cash_balance(user_id) < cost_vnd: return "❌ Ôi Bạn Hết Tiền Rồi!!"

        with db.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Ghi giao dịch chính (Có cột TYPE)
            cursor.execute("""
                INSERT INTO transactions (user_id, asset_type, type, ticker, amount, price, total_value, date) 
                VALUES (?,?,?,?,?,?,?,?)
            """, (user_id, a_type, t_type, ticker, amount, price, total_val, now))
            
            # Tự động ghi đối ứng vào CASH nếu là STOCK/CRYPTO
            if a_type != "CASH":
                cash_type = "OUT" if t_type == "BUY" else "IN"
                cash_impact = -cost_vnd if t_type == "BUY" else cost_vnd
                note = f"{'Mua' if t_type == 'BUY' else 'Bán'} {ticker}"
                cursor.execute("""
                    INSERT INTO transactions (user_id, asset_type, type, ticker, amount, price, total_value, date, note) 
                    VALUES (?, 'CASH', ?, ?, 1, ?, ?, ?, ?)
                """, (user_id, cash_type, f"Ví tiền mặt", cash_impact, cash_impact, now, note))
            
            conn.commit()
        return f"✅ Ghi nhận thành công {t_type} {ticker}. Đã cập nhật ví tiền mặt."

    def _parse_value(self, text):
        clean = text.lower().replace(" ", "").replace(",", ".")
        match = re.search(r"(\d+\.?\d*)", clean)
        if not match: return 0
        num = float(match.group(1))
        if any(x in clean for x in ["ty", "tỷ"]): num *= 10**9
        elif any(x in clean for x in ["tr", "triệu"]): num *= 10**6
        elif "k" in clean: num *= 1000
        elif num < 10000: num *= 10**6
        return num
