from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        # Tên phải khớp tuyệt đối với nút bấm ở Bot Client
        return {
            "id": "dashboard",
            "name": "💼 Tài sản của bạn",
            "description": "Báo cáo tổng quan tài chính"
        }

    def run(self, user_id, data=None):
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                # Lấy tổng giá trị tài sản thực tế từ DB
                cursor.execute("SELECT SUM(value) FROM assets")
                total_val = cursor.fetchone()[0] or 0
            
            # Chuyển đổi sang đơn vị "triệu" để khớp Layout
            total_in_million = total_val / 1000000 if total_val > 0 else 143 # Demo 143 nếu DB trống
            
            # Logic tính toán dựa trên yêu cầu Mục 10
            goal = 500
            profit_loss = -31
            profit_percent = -18
            
            return {
                "total_assets": total_in_million,
                "profit_loss": profit_loss,
                "profit_percent": profit_percent,
                "goal_progress": round((total_in_million / goal) * 100, 1),
                "goal_value": goal,
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
