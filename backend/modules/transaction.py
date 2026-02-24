import re
from datetime import datetime
from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def __init__(self):
        self.states = {} 
        # Danh sách mã mặc định hiểu là Crypto
        self.CRYPTO_TICKERS = ["BTC", "ETH", "BNB", "SOL", "DOT", "ADA", "XRP", "USDT", "LINK", "DOGE"]

    def get_info(self):
        return {"id": "transaction", "name": "➕ Giao dịch"}

    def run(self, user_id, data=None):
        if not data:
            self.states[user_id] = {} 
            return {
                "status": "wizard",
                "message": "📱 *QUẢN LÝ GIAO DỊCH*\nBạn muốn giao dịch gì?",
                "buttons": ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác", "🏠 Trang chủ", "❌ Hủy"]
            }

        # Chuẩn hóa dữ liệu: Xử lý dấu phẩy của người Việt thành dấu chấm cho code hiểu
        text = data.strip().replace(",", ".")
        
        # --- BƯỚC 1: ƯU TIÊN KIỂM TRA LỆNH NHANH (PARSER) ---
        quick_res = self._parse_quick_command(user_id, text)
        if quick_res:
            self.states[user_id] = {} 
            return quick_res

        # --- BƯỚC 2: KIỂM TRA NÚT BẤM MENU ---
        menu_buttons = ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác", "🏠 Trang chủ", "❌ Hủy", "Mua", "Bán", "Nạp", "Rút"]
        if text in menu_buttons:
            if text in ["❌ Hủy", "🏠 Trang chủ"]:
                self.states[user_id] = {}
                return "🏠 Quay lại màn hình chính."
            
            if text in ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác"]:
                self.states[user_id] = {"flow": text, "step": "ask_ticker" if text != "💵 Tiền mặt" else "ask_side"}
                return self._get_wizard_question(text, self.states[user_id])
        
        # --- BƯỚC 3: XỬ LÝ THEO LUỒNG WIZARD ---
        state = self.states.get(user_id, {})
        flow = state.get("flow")
        if flow in ["📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác"]:
            return self._handle_assets_wizard(user_id, text, state)
        if flow == "💵 Tiền mặt":
            return self._handle_cash_wizard(user_id, text, state)

        return "❓ Không rõ yêu cầu. Hãy chọn menu hoặc gõ lệnh nhanh (VD: nap 1ty, btc 0.1 70000)."

    def _get_wizard_question(self, flow, state):
        if flow == "💵 Tiền mặt":
            return {"status": "wizard", "message": "📱 *CASH FLOW*\n➡️ Bạn muốn Nạp hay Rút tiền?", "buttons": ["Nạp", "Rút", "🏠 Trang chủ", "❌ Hủy"]}
        return {"status": "wizard", "message": f"📱 *{flow}*\n➡️ Mã tài sản là gì?", "buttons": ["🏠 Trang chủ", "❌ Hủy"]}

    def _parse_quick_command(self, user_id, text):
        t = text.lower().strip()
        
        # 1. Nhận diện lệnh Tiền mặt
        cash_match = re.search(r"(nạp|nap|rút|rut)\s*(\d+\.?\d*)\s*(tỷ|ty|tr|triệu|k)?", t)
        if cash_match:
            cmd = cash_match.group(1)
            val = self._parse_value(t)
            if val > 0:
                if cmd in ["rút", "rut"]: val = -abs(val)
                return self._save_to_db(user_id, "CASH", "VND", 1, val)

        # 2. Nhận diện lệnh Tài sản (Mã + Số lượng + Giá)
        # Hỗ trợ số lượng thập phân như 0.1
        asset_match = re.match(r"^([a-z0-9]{2,10})\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)$", t)
        if asset_match:
            ticker = asset_match.group(1).upper()
            amount = float(asset_match.group(2))
            price = float(asset_match.group(3))
            
            # TỰ ĐỘNG PHÂN LOẠI CRYPTO VÀ ĐƠN VỊ
            if ticker in self.CRYPTO_TICKERS or len(ticker) > 5:
                a_type = "CRYPTO"
            else:
                a_type = "STOCK"
                # Nếu là Stock và nhập giá thấp (VD: 28.5), tự hiểu là nghìn đồng
                if price < 1000: price *= 1000
                
            return self._save_to_db(user_id, a_type, ticker, amount, price)
        
        return None

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

    def _handle_assets_wizard(self, user_id, text, state):
        step = state.get("step")
        a_map = {"📊 Cổ phiếu": "STOCK", "🪙 Crypto": "CRYPTO", "🥇 Đầu tư khác": "OTHER"}
        a_type = a_map.get(state["flow"], "OTHER")

        if step == "ask_ticker":
            state.update({"ticker": text.upper(), "step": "ask_side"})
            return {"status": "wizard", "message": f"Mã: {text.upper()}\n➡️ Bạn muốn Mua hay Bán?", "buttons": ["Mua", "Bán", "🏠 Trang chủ", "❌ Hủy"]}
        if step == "ask_side":
            if text not in ["Mua", "Bán"]: return "Vui lòng chọn Mua hoặc Bán."
            state.update({"side": 1 if text == "Mua" else -1, "step": "ask_amount"})
            return {"status": "wizard", "message": "➡️ Số lượng bao nhiêu?", "buttons": ["🏠 Trang chủ", "❌ Hủy"]}
        if step == "ask_amount":
            try:
                state.update({"amount": float(text.replace(",", ".")), "step": "ask_price"})
                return {"status": "wizard", "message": "➡️ Giá giao dịch?", "buttons": ["🏠 Trang chủ", "❌ Hủy"]}
            except: return "⚠️ Nhập số lượng bằng con số."
        if step == "ask_price":
            try:
                price = float(text.replace(",", "."))
                # Logic tự quy đổi giá Stock nếu nhập giá thấp trong Wizard
                if a_type == "STOCK" and price < 1000: price *= 1000
                
                res = self._save_to_db(user_id, a_type, state["ticker"], state["amount"] * state["side"], price)
                self.states[user_id] = {}
                return res
            except: return "⚠️ Nhập giá bằng con số."

    def _handle_cash_wizard(self, user_id, text, state):
        step = state.get("step")
        if step == "ask_side":
            if text not in ["Nạp", "Rút"]: return "Vui lòng chọn Nạp hoặc Rút."
            state.update({"side": 1 if text == "Nạp" else -1, "step": "ask_value"})
            return {"status": "wizard", "message": f"➡️ Số tiền {text} bao nhiêu?", "buttons": ["🏠 Trang chủ", "❌ Hủy"]}
        if step == "ask_value":
            val = self._parse_value(text)
            if val == 0: return "⚠️ Số tiền không hợp lệ."
            res = self._save_to_db(user_id, "CASH", "VND", 1, val * state["side"])
            self.states[user_id] = {}
            return res

    def _save_to_db(self, user_id, a_type, ticker, amount, price):
        total = amount * price
        unit = "$" if a_type == "CRYPTO" else "đ"
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (user_id, asset_type, ticker, amount, price, total_value, date) 
                VALUES (?,?,?,?,?,?,?)""",
                (user_id, a_type, ticker, amount, price, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
        
        action = "Mua" if amount > 0 else "Bán"
        if a_type == "CASH": action = "Nạp/Rút"
        
        return f"✅ Đã ghi nhận {action} *{abs(amount)} {ticker}* giá `{price:,.1f}{unit}`. Trang chủ đang cập nhật..."
