from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "dashboard", "name": "💼 Tài sản của bạn"}

    def format_currency(self, value):
        """Hàm định dạng tiền tệ chuyên nghiệp: Nhận giá trị VNĐ thô"""
        abs_val = abs(value)
        if abs_val >= 1000000000:
            return f"{value / 1000000000:,.2f} tỷ"
        elif abs_val >= 1000000:
            return f"{value / 1000000:,.1f} triệu"
        elif abs_val >= 1000:
            return f"{value / 1000:,.0f}k"
        else:
            return f"{value:,.0f}đ"

    def run(self, user_id, data=None):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Lấy tổng giá trị VNĐ thô từ DB
            cursor.execute('''
                SELECT asset_type, SUM(total_value) 
                FROM transactions WHERE user_id = ? GROUP BY asset_type
            ''', (user_id,))
            rows = cursor.fetchall()
            data_map = {row[0]: (row[1] or 0) for row in rows}

            cash_raw = data_map.get('CASH', 0)
            stock_raw = data_map.get('STOCK', 0)
            crypto_raw = data_map.get('CRYPTO', 0)
            other_raw = data_map.get('OTHER', 0)
            
            total_assets_raw = cash_raw + stock_raw + crypto_raw + other_raw
            
            # 2. Tổng nạp / Tổng rút thực tế (VNĐ thô)
            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH' AND total_value > 0", (user_id,))
            total_in_raw = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH' AND total_value < 0", (user_id,))
            total_out_raw = abs(cursor.fetchone()[0] or 0)

            # 3. Tính toán lãi lỗ và mục tiêu
            net_invested = total_in_raw - total_out_raw
            profit_loss_raw = total_assets_raw - net_invested
            profit_percent = (profit_loss_raw / net_invested * 100) if net_invested > 0 else 0
            
            goal_raw = 500000000.0 # 500 triệu VNĐ

            return {
                "display_total": self.format_currency(total_assets_raw),
                "display_profit": self.format_currency(profit_loss_raw),
                "profit_percent": f"{profit_percent:,.1f}%",
                "stock_val": self.format_currency(stock_raw),
                "crypto_val": self.format_currency(crypto_raw),
                "other_val": self.format_currency(other_raw),
                "cash_val": self.format_currency(cash_raw),
                "total_in": self.format_currency(total_in_raw),
                "total_out": self.format_currency(total_out_raw),
                "goal_display": self.format_currency(goal_raw),
                "goal_progress": (total_assets_raw / goal_raw * 100) if goal_raw > 0 else 0,
                "remain_display": self.format_currency(max(0, goal_raw - total_assets_raw))
            }
