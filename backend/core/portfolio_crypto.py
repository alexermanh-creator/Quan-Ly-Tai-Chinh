from backend.database.db_manager import db

class CryptoPortfolio:
    def __init__(self, user_id):
        self.user_id = user_id
        self.usd_rate = 25000  # Tỷ giá mặc định, bạn có thể sửa sau

    def get_data(self):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # Lấy giao dịch crypto
            cursor.execute("""
                SELECT ticker, SUM(CASE WHEN type='BUY' THEN qty ELSE -qty END) as total_qty,
                SUM(CASE WHEN type='BUY' THEN qty*price ELSE 0 END) / SUM(CASE WHEN type='BUY' THEN qty ELSE 0.0001 END) as avg_price
                FROM transactions WHERE user_id = ? AND asset_type = 'CRYPTO'
                GROUP BY ticker HAVING total_qty > 0
            """, (self.user_id,))
            positions = cursor.fetchall()

            # Lấy giá hiện tại
            cursor.execute("SELECT symbol, price_usd FROM crypto_prices")
            prices = {row[0]: row[1] for row in cursor.fetchall()}

            # Tính tổng nạp/rút
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND asset_type = 'CRYPTO' AND type='IN'", (self.user_id,))
            t_in = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND asset_type = 'CRYPTO' AND type='OUT'", (self.user_id,))
            t_out = cursor.fetchone()[0] or 0

        pos_list = []
        total_val_vnd = 0
        total_cost_vnd = 0

        for p in positions:
            ticker, qty, avg_p = p
            curr_p = prices.get(ticker, avg_p)
            val_vnd = qty * curr_p * self.usd_rate
            cost_vnd = qty * avg_p * self.usd_rate
            profit_vnd = val_vnd - cost_vnd
            roi = (profit_vnd / cost_vnd * 100) if cost_vnd > 0 else 0

            pos_list.append({
                'symbol': ticker, 'qty': qty, 'avg_price': avg_p,
                'current_price': curr_p, 'market_value': val_vnd,
                'profit': profit_vnd, 'roi': roi
            })
            total_val_vnd += val_vnd
            total_cost_vnd += cost_vnd

        # Tìm best/worst/largest
        best = max(pos_list, key=lambda x: x['roi']) if pos_list else None
        worst = min(pos_list, key=lambda x: x['roi']) if pos_list else None
        largest = max(pos_list, key=lambda x: x['market_value']) if pos_list else None

        return {
            'summary': {
                'total_value': total_val_vnd, 'total_cost': total_cost_vnd,
                'total_profit': total_val_vnd - total_cost_vnd,
                'total_roi': ((total_val_vnd / total_cost_vnd - 1) * 100) if total_cost_vnd > 0 else 0,
                'best': best, 'worst': worst, 'largest': largest
            },
            'positions': pos_list, 'total_in': t_in, 'total_out': t_out
        }
