import re
from datetime import datetime
from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {
            "id": "transaction",
            "name": "➕ Giao dịch",
            "description": "Quản lý nạp rút và mua bán tài sản"
        }

    def run(self, user_id, data=None):
        # 1. NẾU USER CHƯA NHẬP GÌ (Bấm nút Menu) -> Kích hoạt Wizard
        if not data:
            return {
                "status": "wizard",
                "message": "Bạn muốn giao dịch gì?",
                "buttons": ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Khác", "❌ Hủy"]
            }

        # 2. LOGIC PARSER NHANH (LOCKED)
        text = data.lower().strip()
        
        # Trường hợp A: Nhập cổ phiếu/crypto (Ví dụ: hpg 500 28.5 hoặc btc -0.2 60000)
        # Regex này bóc tách: [mã] [số lượng] [giá]
        match_trade = re.match(r"^([a-z]+)\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)$", text)
        if match_trade:
            ticker = match_trade.group(1).upper()
            amount = float(match_trade.group(2))
            price = float(match_trade.group(3))
            return self._process_quick_trade(user_id, ticker, amount, price)

        # Trường hợp B: Nhập nạp/rút tiền (Ví dụ: nạp 10tr hoặc rút -2tr)
        match_cash = re.search(r"(nạp|rút)?\s*(-?\d+\.?\d*)\s*(tr|k|triệu)?", text)
        if match_cash:
            raw_val = float(match_cash.group(2))
            unit = match_cash.group(3)
            # Quy đổi đơn vị
            if unit == "tr" or unit == "triệu": val = raw_val * 1000000
            elif unit == "k": val = raw_val * 1000
            else: val = raw_val # Giả định nhập số thô
            
            return self._process_quick_cash(user_id, val)

        return "❓ Cú pháp không rõ ràng. Thử lại: `hpg 500 28.5` hoặc `nạp 10tr`"

    def _process_quick_trade(self, user_id, ticker, amount, price):
        """Xử lý lưu vào DB cho giao dịch Stock/Crypto"""
        total_value = (amount * price) # Giá trị giao dịch
        a_type = "STOCK" if len(ticker) <= 4 else "CRYPTO" # Logic phân loại tạm thời
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Lưu vào bảng Transactions (Lịch sử)
            cursor.execute('''
                INSERT INTO transactions (user_id, asset_type, ticker, amount, price, total_value, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, a_type, ticker, amount, price, total_value, datetime.now().strftime("%Y-%m-%d")))
            
            # 2. Cập nhật bảng Assets (Số dư hiện tại)
            # Lưu ý: Ở đây ta cộng dồn giá trị vào Asset_type để dashboard hiển thị
            cursor.execute("INSERT OR IGNORE INTO assets (asset_type, value) VALUES (?, 0)", (a_type,))
            cursor.execute("UPDATE assets SET value = value + ? WHERE asset_type = ?", (total_value, a_type))
            conn.commit()
            
        action = "MUA" if amount > 0 else "BÁN"
        return f"✅ Đã ghi nhận {action} {abs(amount)} {ticker} giá {price:,.0f}. (Dữ liệu đã được bảo toàn)"

    def _process_quick_cash(self, user_id, value):
        """Xử lý nạp rút tiền mặt"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, asset_type, ticker, amount, total_value, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, "CASH", "VND", 1, value, datetime.now().strftime("%Y-%m-%d")))
            
            cursor.execute("INSERT OR IGNORE INTO assets (asset_type, value) VALUES (?, 0)", ("CASH",,))
            cursor.execute("UPDATE assets SET value = value + ? WHERE asset_type = ?", (value, "CASH"))
            conn.commit()
            
        return f"✅ Đã ghi nhận {'NẠP' if value > 0 else 'RÚT'}: {abs(value/1000000):,.1f} triệu VNĐ."
