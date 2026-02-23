import re
from datetime import datetime
from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def __init__(self):
        self.states = {} 

    def get_info(self):
        return {"id": "transaction", "name": "➕ Giao dịch"}

    def run(self, user_id, data=None):
        # 1. KHỞI TẠO MENU CHÍNH
        if not data:
            self.states[user_id] = {} 
            return {
                "status": "wizard",
                "message": "📱 *QUẢN LÝ GIAO DỊCH*\nBạn muốn giao dịch gì?",
                "buttons": ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác", "🏠 Trang chủ", "❌ Hủy"]
            }

        text = data.strip()
        menu_buttons = ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác", "🏠 Trang chủ", "❌ Hủy", "Mua", "Bán"]
        
        # 2. ƯU TIÊN KIỂM TRA NÚT BẤM TRƯỚC (Để tránh lỗi Parser chặn nút)
        if text in menu_buttons:
            if text == "❌ Hủy" or text == "🏠 Trang chủ":
                self.states[user_id] = {}
                return "🏠 Quay lại màn hình chính." # Bot_client sẽ nhận diện chữ này để hiện Dashboard

            # Reset state khi chọn luồng giao dịch mới
            if text in ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác"]:
                self.states[user_id] = {"flow": text, "step": "ask_ticker" if text != "💵 Tiền mặt" else "ask_side"}

        # 3. CHỈ CHẠY PARSER NHANH NẾU KHÔNG PHẢI ĐANG BẤM NÚT MENU
        else:
            quick_res = self._parse_quick_command(user_id, text)
            if quick_res:
                self.states[user_id] = {}
                return quick_res

        state = self.states.get(user_id, {})
        flow = state.get("flow")

        # 4. ĐIỀU HƯỚNG WIZARD
        if flow in ["📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác"]:
            return self._handle_assets_wizard(user_id, text, state)
        if flow == "💵 Tiền mặt":
            return self._handle_cash_wizard(user_id, text, state)

        return "❓ Cú pháp chưa đúng. Hãy chọn menu hoặc nhập lệnh nhanh (VD: hpg 100 28.5)."

    def _handle_assets_wizard(self, user_id, text, state):
        step = state.get("step")
        a_map = {"📊 Cổ phiếu": "STOCK", "🪙 Crypto": "CRYPTO", "🥇 Đầu tư khác": "OTHER"}
        a_type = a_map.get(state["flow"], "OTHER")

        if text == state["flow"]:
            return {
                "status": "wizard",
                "message": f"📱 *{a_type} FLOW*\n➡️ Mã tài sản là gì?",
                "buttons": ["🏠 Trang chủ", "❌ Hủy"]
            }

        if step == "ask_ticker":
            state.update({"ticker": text.upper(), "step": "ask_side"})
            return {
                "status": "wizard",
                "message": f"Mã: {text.upper()}\n➡️ Bạn muốn Mua hay Bán?",
                "buttons": ["Mua", "Bán", "🏠 Trang chủ", "❌ Hủy"]
            }

        if step == "ask_side":
            if text not in ["Mua", "Bán"]: return "Vui lòng chọn Mua hoặc Bán."
            state.update({"side": 1 if text == "Mua" else -1, "step": "ask_amount"})
            return {
                "status": "wizard",
                "message": f"➡️ Số lượng {'Mua' if text=='Mua' else 'Bán'} là bao nhiêu?",
                "buttons": ["🏠 Trang chủ", "❌ Hủy"]
            }

        if step == "ask_amount":
            try:
                state.update({"amount": float(text), "step": "ask_price"})
                return {"status": "wizard", "message": "➡️ Giá giao dịch?", "buttons": ["🏠 Trang chủ", "❌ Hủy"]}
            except: return "⚠️ Nhập số lượng bằng con số."

        if step == "ask_price":
            try:
                res = self._save_to_db(user_id, a_type, state["ticker"], state["amount"] * state["side"], float(text))
                self.states[user_id] = {}
                return res
            except: return "⚠️ Nhập giá bằng con số."

    def _handle_cash_wizard(self, user_id, text, state):
        step = state.get("step")
        if text == "💵 Tiền mặt":
            return {
                "status": "wizard",
                "message": "📱 *CASH FLOW*\n➡️ Nạp hay Rút tiền?",
                "buttons": ["Nạp", "Rút", "🏠 Trang chủ", "❌ Hủy"]
            }
        if step == "ask_side":
            if text not in ["Nạp", "Rút"]: return "Vui lòng chọn Nạp hoặc Rút."
            state.update({"side": 1 if text == "Nạp" else -1, "step": "ask_value"})
            return {"status": "wizard", "message": "➡️ Số tiền bao nhiêu?", "buttons": ["🏠 Trang chủ", "❌ Hủy"]}
        if step == "ask_value":
            val = self._parse_value(text)
            if val == 0: return "⚠️ Số tiền không hợp lệ."
            res = self._save_to_db(user_id, "CASH", "VND", 1, val * state["side"])
            self.states[user_id] = {}
            return res

    def _save_to_db(self, user_id, a_type, ticker, amount, price=1):
        total = amount * price
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (user_id, asset_type, ticker, amount, price, total_value, date) VALUES (?,?,?,?,?,?,?)",
                           (user_id, a_type, ticker, amount, price, total, datetime.now().strftime("%Y-%m-%d")))
            cursor.execute("INSERT OR IGNORE INTO assets (asset_type, value) VALUES (?, 0)", (a_type,))
            cursor.execute("UPDATE assets SET value = value + ? WHERE asset_type = ?", (total, a_type))
            conn.commit()
        return f"✅ Ghi nhận thành công {ticker}. Bấm 🏠 Trang chủ để xem Dashboard."

    def _parse_quick_command(self, user_id, text):
        t = text.lower().strip()
        asset_match = re.match(r"^([a-z]{2,10})\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)$", t)
        if asset_match:
            ticker = asset_match.group(1).upper()
            a_type = "CRYPTO" if ticker in ["BTC", "ETH"] or len(ticker) > 4 else "STOCK"
            return self._save_to_db(user_id, a_type, ticker, float(asset_match.group(2)), float(asset_match.group(3)))
        if any(kw in t for kw in ["nạp", "rút", "tr", "k"]):
            val = self._parse_value(t)
            if val != 0:
                if "rút" in t: val = -abs(val)
                return self._save_to_db(user_id, "CASH", "VND", 1, val)
        return None

    def _parse_value(self, text):
        clean = text.lower().replace(" ", "")
        match = re.search(r"(\d+\.?\d*)", clean)
        if not match: return 0
        num = float(match.group(1))
        if "tr" in clean or "triệu" in clean: num *= 1000000
        elif "k" in clean: num *= 1000
        return num
