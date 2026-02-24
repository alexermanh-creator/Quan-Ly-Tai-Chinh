from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "dashboard", "name": "💼 Tài sản của bạn"}

    def format_currency(self, value):
        abs_val = abs(value)
        sign = "-" if value < 0 else ""
        if abs_val >= 1000000000:
            return f"{sign}{abs_val / 1000000000:,.2f} tỷ"
        elif abs_val >= 1000000:
            return f"{sign}{abs_val / 1000000:,.1f} triệu"
        else:
            return f"{sign}{abs_val:,.0f}đ"

    def run(self, user_id, data=None):
        EXCHANGE_RATE_USD = 26300 
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT asset_type, SUM(total_value) FROM transactions WHERE user_id = ? GROUP BY asset_type', (user_id,))
            data_map = {row[0]: (row[1] or 0) for row in cursor.fetchall()}

            cash = data_map.get('CASH', 0)
            stock = data_map.get('STOCK', 0)
            crypto_vnd = data_map.get('CRYPTO', 0) * EXCHANGE_RATE_USD
            other = data_map.get('OTHER', 0)
            total = cash + stock + crypto_vnd + other

            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH' AND total_value > 0", (user_id,))
            t_in = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(total_value) FROM transactions WHERE user_id = ? AND asset_type = 'CASH' AND total_value < 0", (user_id,))
            t_out = abs(cursor.fetchone()[0] or 0)

            net_invested = t_in - t_out
            profit = total - net_invested
            roi = (profit / net_invested * 100) if net_invested > 0 else 0

            return {
                "display_total": self.format_currency(total),
                "display_profit": self.format_currency(profit),
                "profit_percent": f"{roi:+.1f}%",
                "stock_val": self.format_currency(stock),
                "crypto_val": self.format_currency(crypto_vnd),
                "cash_val": self.format_currency(cash),
                "other_val": self.format_currency(other),
                "total_in": self.format_currency(t_in),
                "total_out": self.format_currency(t_out),
                "goal_display": "500.0 triệu",
                "goal_progress": (total / 500000000 * 100),
                "remain_display": self.format_currency(max(0, 500000000 - total))
            }
