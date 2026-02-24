from backend.database.db_manager import db

class CryptoPortfolio:
    def __init__(self, user_id):
        self.user_id = user_id
        self.usd_rate = 25400  # Tỷ giá cập nhật

    def get_data(self):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Lấy danh mục Crypto (Sửa qty thành amount cho khớp db)
            cursor.execute("""
                SELECT ticker, 
                SUM(CASE WHEN type='BUY' THEN amount ELSE -amount END) as total_qty,
                SUM(CASE WHEN type='BUY' THEN amount*price ELSE 0 END) / 
                NULLIF(SUM(CASE WHEN type='BUY' THEN amount ELSE 0 END), 0) as avg_price
                FROM transactions 
                WHERE user_id = ? AND asset_type = 'CRYPTO'
                GROUP BY ticker 
                HAVING total_qty > 0
            """, (self.user_id,))
            positions = cursor.fetchall()

            # 2. Lấy giá hiện tại
            cursor.execute("SELECT symbol, price_usd FROM crypto_prices")
            prices = {row[0]: row[1] for row in cursor.fetchall()}

            # 3. Tính tổng nạp/rút (Sử dụng cột total_value làm số tiền)
            cursor.execute("""
                SELECT 
                SUM(CASE WHEN type='IN' THEN total_value ELSE 0 END),
                SUM(CASE WHEN type='OUT' THEN total_value ELSE 0 END)
                FROM transactions WHERE user_id = ? AND asset_type = 'CRYPTO'
            """, (self.user_id,))
            t_in_out = cursor.fetchone()
            t_in = t_in_out[0] or 0
            t_out = t_in_out[1] or 0

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
