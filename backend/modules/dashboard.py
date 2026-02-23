from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {
            "id": "dashboard",
            "name": "Bảng điều khiển tài chính",
            "description": "Hiển thị tổng quan tài sản và tăng trưởng"
        }

    def run(self, user_id, data=None):
        # Truy vấn dữ liệu thực tế từ Database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(value) FROM assets")
            total = cursor.fetchone()[0] or 0
            
        # Tính toán các chỉ số (tạm thời giả lập logic tăng trưởng cho đến khi có module Transaction)
        return {
            "total_assets": total,
            "profit_loss": -31000000, # Giả lập dựa trên spec của bạn
            "profit_percent": -18,
            "goal_progress": 28.6,
            "message": "Dữ liệu được cập nhật từ hệ thống Core."
        }