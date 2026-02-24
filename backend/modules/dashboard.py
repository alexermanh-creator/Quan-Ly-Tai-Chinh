import re
from datetime import datetime
from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def __init__(self):
        self.states = {} 
        self.CRYPTO_TICKERS = ["BTC", "ETH", "BNB", "SOL", "DOT", "ADA", "XRP", "USDT", "LINK", "DOGE"]
        self.EXCHANGE_RATE_USD = 26300 # Tỷ giá đồng bộ với Dashboard

    def get_info(self):
        return {"id": "transaction", "name": "➕ Giao dịch"}

    def _get_cash_balance(self, user_id):
        """Tính số dư tiền mặt hiện tại trong ví"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH'", (user_id,))
            return cursor.fetchone()[0] or 0

    def run(self, user_id, data=None):
        if not data:
            self.states[user_id] = {} 
            return {
                "status": "wizard",
                "message": "📱 *QUẢN LÝ GIAO DỊCH*\nBạn muốn giao dịch gì?",
                "buttons": ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Đầu tư khác", "🏠 Trang chủ", "❌ Hủy"]
            }

        text = data.strip().replace(",", ".")
        quick_res = self._parse_quick_command(user_id, text)
        if quick_res:
            self.states[user_id] = {} 
            return quick_res

        # --- LOGIC WIZARD VÀ MENU GIỮ NGUYÊN ---
        # (Để tiết kiệm không gian, tôi tập trung vào phần logic Save bên dưới)
        # ... [Giữ các hàm _get_wizard_question, _handle_assets_wizard, v.v.] ...
        
        # Lưu ý: Trong các hàm handle_wizard, khi gọi self._save_to_db, logic mới sẽ tự áp dụng.
        return self._handle_logic_flow(user_id, text) # Hàm giả định điều hướng tiếp

    def _parse_quick_command(self, user_id, text):
        t = text.lower().strip()
        
        # 1. Lệnh Tiền mặt (Nạp/Rút trực tiếp vào ví)
        cash_match = re.search(r"(nạp|nap|rút|rut)\s*(\d+\.?\d*)\s*(tỷ|ty|tr|triệu|k)?", t)
        if cash_match:
            cmd = cash_match.group(1)
            val = self._parse_value(t)
            if val > 0:
                if cmd in ["rút", "rut"]:
                    current_balance = self._get_cash_balance(user_id)
                    if current_balance < val: return "❌ Ôi Bạn Hết Tiền Rồi!!"
                    val = -abs(val)
                return self._save_to_db(user_id, "CASH", "VND", 1, val)

        # 2. Lệnh Tài sản (Mua Stock/Crypto -> Trừ tiền ví)
        asset_match = re.match(r"^([a-z0-9]{2,10})\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)$", t)
        if asset_match:
            ticker = asset_match.group(1).upper()
            amount = float(asset_match.group(2))
            price = float(asset_match.group(3))
            
            if ticker in self.CRYPTO_TICKERS or len(ticker) > 5:
                a_type = "CRYPTO"
            else:
                a_type = "STOCK"
                if price < 1000: price *= 1000
                
            return self._save_to_db(user_id, a_type, ticker, amount, price)
        return None

    def _save_to_db(self, user_id, a_type, ticker, amount, price):
        total_value = amount * price
        
        # QUY ĐỔI GIÁ TRỊ SANG VND ĐỂ KIỂM TRA VÍ TIỀN MẶT
        cost_in_vnd = total_value
        if a_type == "CRYPTO":
            cost_in_vnd = total_value * self.EXCHANGE_RATE_USD

        # KIỂM TRA SỐ DƯ KHI MUA (AMOUNT > 0)
        if a_type != "CASH" and amount > 0:
            current_balance = self._get_cash_balance(user_id)
            if current_balance < cost_in_vnd:
                return "❌ Ôi Bạn Hết Tiền Rồi!!"

        with db.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 1. Ghi nhận giao dịch tài sản
            cursor.execute("""
                INSERT INTO transactions (user_id, asset_type, ticker, amount, price, total_value, date) 
                VALUES (?,?,?,?,?,?,?)""",
                (user_id, a_type, ticker, amount, price, total_value, now))
            
            # 2. NẾU LÀ MUA TÀI SẢN -> TỰ ĐỘNG TẠO LỆNH RÚT TIỀN MẶT (TRỪ VÍ)
            if a_type != "CASH":
                # Mua thì trừ tiền (cash_impact âm), Bán thì cộng tiền (cash_impact dương)
                cash_impact = -cost_in_vnd 
                cursor.execute("""
                    INSERT INTO transactions (user_id, asset_type, ticker, amount, price, total_value, date) 
                    VALUES (?, 'CASH', ?, 1, ?, ?, ?)""",
                    (user_id, f"Mua/Bán {ticker}", cash_impact, cash_impact, now))
            
            conn.commit()
        
        unit = "$" if a_type == "CRYPTO" else "đ"
        return f"✅ Giao dịch thành công! Đã chiết khấu từ ví tiền mặt. Trang chủ đang cập nhật..."

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
