import re
from datetime import datetime
from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def __init__(self):
        # Bộ nhớ tạm để quản lý trạng thái cho từng user
        self.states = {} 

    def get_info(self):
        return {"id": "transaction", "name": "➕ Giao dịch"}

    def run(self, user_id, data=None):
        if not data:
            self.states[user_id] = {} 
            return {
                "status": "wizard",
                "message": "Bạn muốn giao dịch gì?",
                "buttons": ["📊 Cổ phiếu", "🪙 Crypto", "💵 Tiền mặt", "🥇 Khác", "❌ Hủy"]
            }

        text = data.strip()
        state = self.states.get(user_id, {})

        if text == "❌ Hủy":
            self.states[user_id] = {}
            return "✅ Đã hủy giao dịch."

        # ĐIỀU HƯỚNG THEO LOẠI TÀI SẢN
        if text == "📊 Cổ phiếu" or state.get('flow') == 'STOCK':
            return self._handle_assets_wizard(user_id, text, state, "STOCK")
        
        if text == "🪙 Crypto" or state.get('flow') == 'CRYPTO':
            return self._handle_assets_wizard(user_id, text, state, "CRYPTO")

        if text == "🥇 Khác" or state.get('flow') == 'OTHER':
            return self._handle_assets_wizard(user_id, text, state, "OTHER")

        if text == "💵 Tiền mặt" or state.get('flow') == 'CASH':
            return self._handle_cash_wizard(user_id, text, state)

        # PHẦN PARSER NHANH (BẢO TOÀN LỆNH TẮT)
        return self._parse_quick_command(user_id, text)

    # WIZARD DÙNG CHUNG CHO STOCK, CRYPTO, KHÁC
    def _handle_assets_wizard(self, user_id, text, state, flow_type):
        step = state.get('step', 'start')
        
        if step == 'start':
            self.states[user_id] = {'flow': flow_type, 'step': 'ask_ticker'}
            prompts = {"STOCK": "Mã chứng khoán?", "CRYPTO": "Mã Crypto (BTC, ETH...)?", "OTHER": "Tên tài sản (Vàng, Đất... )?"}
            return prompts[flow_type]

        if step == 'ask_ticker':
            self.states[user_id].update({'ticker': text.upper(), 'step': 'ask_side'})
            return {
                "status": "wizard",
                "message": f"Tài sản {text.upper()}: Bạn muốn Mua hay Bán?",
                "buttons": ["Mua", "Bán", "❌ Hủy"]
            }

        if step == 'ask_side':
            side = 1 if text == "Mua" else -1
            self.states[user_id].update({'side': side, 'step': 'ask_amount'})
            return f"Số lượng {'Mua' if side==1 else 'Bán'} là bao nhiêu?"

        if step == 'ask_amount':
            try:
                self.states[user_id].update({'amount': float(text), 'step': 'ask_price'})
                return "Giá giao dịch là bao nhiêu?"
            except: return "⚠️ Vui lòng nhập số lượng bằng con số."

        if step == 'ask_price':
            try:
                s = self.states[user_id]
                res = self._save_to_db(user_id, s['flow'], s['ticker'], s['amount'] * s['side'], float(text))
                self.states[user_id] = {}
                return res
            except: return "⚠️ Vui lòng nhập giá bằng con số."

    # WIZARD CHO TIỀN MẶT
    def _handle_cash_wizard(self, user_id, text, state):
        if state.get('step') != 'ask_value':
            self.states[user_id] = {'flow': 'CASH', 'step': 'ask_value'}
            return {
                "status": "wizard",
                "message": "Chọn loại giao dịch tiền mặt:",
                "buttons": ["Nạp tiền", "Rút tiền", "❌ Hủy"]
            }
        
        # Xử lý nhập giá trị tiền
        is_rut = "rút" in text.lower()
        val = self._parse_value(text)
        if val == 0: return "⚠️ Vui lòng nhập số tiền (VD: 10tr hoặc nạp 5tr)."
        
        final_val = -val if is_rut else val
        res = self._save_to_db(user_id, "CASH", "VND", 1, final_val)
        self.states[user_id] = {}
        return res

    def _save_to_db(self, user_id, a_type, ticker, amount, price):
        total = amount * price
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, asset_type, ticker, amount, price, total_value, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, a_type, ticker, amount, price, total, datetime.now().strftime("%Y-%m-%d")))
            
            cursor.execute("INSERT OR IGNORE INTO assets (asset_type, value) VALUES (?, 0)", (a_type,))
            cursor.execute("UPDATE assets SET value = value + ? WHERE asset_type = ?", (total, a_type))
            conn.commit()
        return f"✅ Đã ghi nhận {a_type}: {ticker} ({'Mua/Nạp' if amount > 0 else 'Bán/Rút'}). Số dư đã cập nhật."

    def _parse_quick_command(self, user_id, text):
        t = text.lower()
        # Parser nhanh Stock/Crypto: hpg 100 28.5 hoặc btc 0.1 50000
        m = re.match(r"^([a-z]+)\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)$", t)
        if m:
            ticker = m.group(1).upper()
            a_type = "CRYPTO" if len(ticker) > 5 or ticker in ["BTC", "ETH", "USDT"] else "STOCK"
            return self._save_to_db(user_id, a_type, ticker, float(m.group(2)), float(m.group(3)))
        
        # Parser nhanh Tiền mặt: nạp 10tr
        val = self._parse_value(t)
        if val != 0:
            if "rút" in t: val = -val
            return self._save_to_db(user_id, "CASH", "VND", 1, val)
        
        return "❓ Không rõ yêu cầu. Hãy chọn nút bấm hoặc nhập lệnh nhanh (VD: hpg 100 28)."

    def _parse_value(self, text):
        clean = text.replace("nạp","").replace("rút","").replace("tr","000000").replace("k","000").replace("triệu","000000").strip()
        nums = re.findall(r"\d+\.?\d*", clean)
        return float(nums[0]) if nums else 0
