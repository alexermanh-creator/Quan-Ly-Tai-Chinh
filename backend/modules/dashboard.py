from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "dashboard", "name": "💼 Tài sản của bạn"}

    def format_currency(self, value_in_million):
        """Hàm định dạng tiền tệ chuyên nghiệp: Tự động chuyển Tỷ/Triệu/Đồng"""
        val = value_in_million * 1000000
        abs_val = abs(val)
        
        if abs_val >= 1000000000:
            return f"{val / 1000000000:,.2f} tỷ"
        elif abs_val >= 1000000:
            return f"{val / 1000000:,.1f} triệu"
        elif abs_val >= 1000:
            return f"{val / 1000:,.0f}k"
        else:
            return f"{val:,.0f}đ"

    def run(self, user_id, data=None):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Lấy số dư hiện tại từ Database
            cursor.execute('''
                SELECT asset_type, SUM(total_value) 
                FROM transactions 
                WHERE user_id = ? 
                GROUP BY asset_type
            ''', (user_id,))
            rows = cursor.fetchall()
            data_map = {row[0]: row[1] for row in rows}

            # Quy đổi đơn vị cơ sở ra Triệu để tính toán nội bộ
            cash_val = data_map.get('CASH', 0) / 1000000
            stock_val = data_map.get('STOCK', 0) / 1000000
            crypto_val = data_map.get('CRYPTO', 0) / 1000000
            other_val = data_map.get('OTHER', 0) / 1000000
            
            # 2. Tính Tổng nạp / Tổng rút thực tế (Chỉ từ dòng tiền CASH)
            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH' AND total_value > 0", (user_id,))
            total_in_raw = (cursor.fetchone()[0] or 0) / 1000000
            
            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH' AND total_value < 0", (user_id,))
            total_out_raw = abs((cursor.fetchone()[0] or 0) / 1000000)

            # 3. Các chỉ số tổng hợp
            total_assets = cash_val + stock_val + crypto_val + other_val
            goal_value = 500.0 # Mục tiêu 500 triệu
            
            net_invested = total_in_raw - total_out_raw
            profit_loss = total_assets - net_invested
            profit_percent = (profit_loss / net_invested * 100) if net_invested > 0 else 0

            # 4. Trả về dữ liệu ĐÃ ĐỊNH DẠNG CHUỖI cho Bot hiển thị
            return {
                "display_total": self.format_currency(total_assets),
                "display_profit": self.format_currency(profit_loss),
                "profit_percent": f"{profit_percent:,.1f}%",
                
                "stock_val": self.format_currency(stock_val),
                "crypto_val": self.format_currency(crypto_val),
                "other_val": self.format_currency(other_val),
                "cash_val": self.format_currency(cash_val),
                
                "total_in": self.format_currency(total_in_raw),
                "total_out": self.format_currency(total_out_raw),
                
                "goal_display": self.format_currency(goal_value),
                "goal_progress": (total_assets / goal_value * 100) if goal_value > 0 else 0,
                "remain_display": self.format_currency(max(0, goal_value - total_assets))
            }
