from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "dashboard", "name": "💼 Tài sản của bạn"}

    def run(self, user_id, data=None):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Lấy số dư hiện tại của từng loại tài sản
            cursor.execute('''
                SELECT asset_type, SUM(total_value) 
                FROM transactions 
                WHERE user_id = ? 
                GROUP BY asset_type
            ''', (user_id,))
            rows = cursor.fetchall()
            data_map = {row[0]: row[1] for row in rows}

            # 2. Quy đổi đơn vị (VND -> Triệu)
            # Chúng ta dùng .get() để nếu chưa có giao dịch nào thì trả về 0
            cash_val = data_map.get('CASH', 0) / 1000000
            stock_val = data_map.get('STOCK', 0) / 1000000
            crypto_val = data_map.get('CRYPTO', 0) / 1000000
            other_val = data_map.get('OTHER', 0) / 1000000
            
            # 3. Tính Tổng nạp & Tổng rút thực tế từ tiền mặt
            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH' AND total_value > 0", (user_id,))
            total_in = (cursor.fetchone()[0] or 0) / 1000000
            
            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH' AND total_value < 0", (user_id,))
            total_out = abs((cursor.fetchone()[0] or 0) / 1000000)

            # 4. Tính toán các chỉ số Dashboard Mục 10
            total_assets = cash_val + stock_val + crypto_val + other_val
            goal_value = 500 # Mục tiêu của bạn
            
            # Tính Lãi/Lỗ: Tài sản hiện có - (Tiền thực nạp - Tiền thực rút)
            net_invested = total_in - total_out
            profit_loss = total_assets - net_invested
            profit_percent = (profit_loss / net_invested * 100) if net_invested != 0 else 0

            return {
                "total_assets": total_assets,
                "profit_loss": profit_loss,
                "profit_percent": profit_percent,
                "stock_val": stock_val,
                "crypto_val": crypto_val,
                "other_val": other_val,
                "cash_val": cash_val,
                "total_in": total_in,
                "total_out": total_out,
                "goal_value": goal_value,
                "goal_progress": (total_assets / goal_value * 100) if goal_value > 0 else 0
            }
