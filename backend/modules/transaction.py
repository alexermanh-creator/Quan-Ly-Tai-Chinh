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
        # 1. NẾU USER CHƯA NHẬP GÌ (Bấm nút Menu chính ➕ Giao dịch)
        if not data:
            return {
                "status": "wizard",
                "message": "Bạn muốn giao dịch gì?",
                "buttons": ["💵 Tiền mặt", "📊 Cổ phiếu", "🪙 Crypto", "🥇 Khác", "❌ Hủy"]
            }

        text = data.strip() # Giữ nguyên hoa thường để khớp nút bấm có icon

        # 2. XỬ LÝ CÁC NÚT BẤM WIZARD (Ưu tiên kiểm tra trước)
        if text == "💵 Tiền mặt":
            return "📱 *CASH FLOW*\nVui lòng nhập: `nạp [số tiền]` hoặc `rút [số tiền]`\nVí dụ: `nạp 10tr` hoặc `rút 5tr`"
        
        if text == "📊 Cổ phiếu":
            return "📱 *STOCK FLOW*\nVui lòng nhập: `[mã] [số lượng] [giá]`\nVí dụ: `fpt 100 85` hoặc `hpg -500 28.5` (Bán)"
            
        if text == "❌ Hủy":
            return "✅ Đã hủy lệnh giao dịch."

        # 3. LOGIC PARSER NHANH (Chỉ chạy khi không phải bấm nút trên)
        text_lower = text.lower()
        
        # Cổ phiếu/Crypto
        match_trade = re.match(r"^([a-z]+)\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)$", text_lower)
        if match_trade:
            ticker = match_trade.group(1).upper()
            amount = float(match_trade.group(2))
            price = float(match_trade.group(3))
            return self._process_quick_trade(user_id, ticker, amount, price)

        # Tiền mặt
        match_cash = re.search(r"(nạp|rút)?\s*(-?\d+\.?\d*)\s*(tr|k|triệu)?", text_lower)
        if match_cash:
            raw_val = float(match_cash.group(2))
            unit = match_cash.group(3)
            # Logic xử lý đơn vị
            val = raw_val
            if unit in ["tr", "triệu"]: val = raw_val * 1000000
            elif unit == "k": val = raw_val * 1000
            
            # Nếu người dùng nhập "rút 2tr" nhưng quên dấu âm, ta tự thêm dấu âm
            if "rút" in text_lower and val > 0: val = -val
                
            return self._process_quick_cash(user_id, val)

        return "❓ Cú pháp không rõ ràng. Thử lại: `hpg 500 28.5` hoặc chọn nút chức năng."

    def _process_quick_cash(self, user_id, value):
        """Xử lý nạp rút tiền mặt - Đã fix lỗi Syntax"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Lưu giao dịch
            cursor.execute('''
                INSERT INTO transactions (user_id, asset_type, ticker, amount, total_value, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, "CASH", "VND", 1, value, datetime.now().strftime("%Y-%m-%d")))
            
            # 2. Cập nhật số dư tài sản
            cursor.execute("INSERT OR IGNORE INTO assets (asset_type, value) VALUES (?, 0)", ("CASH",))
            cursor.execute("UPDATE assets SET value = value + ? WHERE asset_type = ?", (value, "CASH"))
            conn.commit()
            
        return f"✅ Đã ghi nhận {'NẠP' if value > 0 else 'RÚT'}: {abs(value/1000000):,.1f} triệu VNĐ."
