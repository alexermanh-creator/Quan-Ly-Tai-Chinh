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
    "total_assets": total / 1000000, # Chia 1 triệu để hiển thị đúng đơn vị bạn muốn
    "profit_loss": -31,             # Thêm để khớp Layout mục 10
    "profit_percent": -18,          # Thêm để khớp Layout mục 10
    "goal_progress": 28.6,          # Thêm để khớp Layout mục 10
    "message": "Cập nhật từ hệ thống Core"
}
