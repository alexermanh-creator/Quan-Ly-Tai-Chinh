from backend.database.db_manager import db
from backend.core.analytics import StockAnalytics

class PortfolioManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.analytics = StockAnalytics()

    def get_stock_portfolio(self):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ticker, amount, price, total_value 
                FROM transactions 
                WHERE user_id = ? AND asset_type = 'STOCK'
                ORDER BY date ASC
            ''', (self.user_id,))
            records = cursor.fetchall()

        portfolio = {}
        total_in = 0
        total_out = 0

        for ticker, amount, price, total_val in records:
            if ticker not in portfolio:
                portfolio[ticker] = {'qty': 0, 'cost': 0, 'last_price': 0}
            
            portfolio[ticker]['qty'] += amount
            portfolio[ticker]['last_price'] = abs(price) # Lấy giá giao dịch cuối làm giá hiện tại
            
            if amount > 0:
                portfolio[ticker]['cost'] += abs(total_val)
                total_in += abs(total_val)
            else:
                # Khi bán, giảm vốn theo tỷ lệ
                avg_cost_before = portfolio[ticker]['cost'] / (portfolio[ticker]['qty'] - amount)
                portfolio[ticker]['cost'] -= abs(amount * avg_cost_before)
                total_out += abs(total_val)

        positions = []
        for ticker, data in portfolio.items():
            if data['qty'] <= 0: continue 

            current_price = data['last_price'] 
            market_value = data['qty'] * current_price
            avg_price = data['cost'] / data['qty'] if data['qty'] > 0 else 0
            
            positions.append({
                'ticker': ticker,
                'qty': data['qty'],
                'avg_price': avg_price,
                'current_price': current_price,
                'cost': data['cost'],
                'market_value': market_value,
                'profit': market_value - data['cost'],
                'roi': self.analytics.calculate_roi(data['cost'], market_value)
            })

        return {
            'positions': positions,
            'total_in': total_in,
            'total_out': total_out,
            'summary': self._calculate_summary(positions)
        }

    def _calculate_summary(self, positions):
        total_cost = sum(p['cost'] for p in positions)
        total_value = sum(p['market_value'] for p in positions)
        return {
            'total_cost': total_cost,
            'total_value': total_value,
            'total_profit': total_value - total_cost,
            'total_roi': self.analytics.calculate_roi(total_cost, total_value),
            'best': self.analytics.get_best_performer(positions),
            'worst': self.analytics.get_worst_performer(positions),
            'largest': self.analytics.get_largest_weight(positions)
        }
