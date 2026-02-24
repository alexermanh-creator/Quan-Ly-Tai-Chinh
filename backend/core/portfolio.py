from backend.database.db_manager import db
from backend.core.analytics import StockAnalytics

class PortfolioManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.analytics = StockAnalytics()
        self.usd_rate = 26300  # Tỷ giá chuẩn đồng bộ toàn hệ thống

    def get_stock_portfolio(self):
        return self._get_asset_portfolio(asset_type='STOCK', price_table='stock_prices')

    def get_crypto_portfolio(self):
        return self._get_asset_portfolio(asset_type='CRYPTO', price_table='crypto_prices', is_crypto=True)

    def _get_asset_portfolio(self, asset_type, price_table, is_crypto=False):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Lấy giá thị trường hiện tại
            price_col = 'price_usd' if is_crypto else 'current_price'
            cursor.execute(f"SELECT UPPER(ticker), {price_col} FROM {price_table}")
            market_prices = {row[0]: row[1] for row in cursor.fetchall()}

            # 2. Lấy toàn bộ lịch sử giao dịch
            cursor.execute(f'''
                SELECT UPPER(ticker), amount, price, total_value, COALESCE(UPPER(type), 'BUY') 
                FROM transactions 
                WHERE user_id = ? AND UPPER(asset_type) = UPPER(?)
                ORDER BY date ASC
            ''', (self.user_id, asset_type))
            records = cursor.fetchall()

        portfolio = {}
        total_buy_val = 0
        total_sell_val = 0

        for ticker, amount, price, total_val, t_type in records:
            if ticker not in portfolio:
                portfolio[ticker] = {'qty': 0, 'cost_usd': 0, 'last_price': abs(price)}
            
            portfolio[ticker]['last_price'] = abs(price)
            
            if t_type in ['BUY', 'IN']:
                portfolio[ticker]['qty'] += abs(amount)
                portfolio[ticker]['cost_usd'] += abs(total_val)
                total_buy_val += abs(total_val) * (self.usd_rate if is_crypto else 1)
            elif t_type in ['SELL', 'OUT']:
                if portfolio[ticker]['qty'] > 0:
                    avg_cost_usd = portfolio[ticker]['cost_usd'] / portfolio[ticker]['qty']
                    portfolio[ticker]['cost_usd'] -= abs(amount) * avg_cost_usd
                    portfolio[ticker]['qty'] -= abs(amount)
                total_sell_val += abs(total_val) * (self.usd_rate if is_crypto else 1)

        positions = []
        rate = self.usd_rate if is_crypto else 1

        for ticker, data in portfolio.items():
            if data['qty'] > 0.00000001: 
                current_p = market_prices.get(ticker, data['last_price'])
                market_value_vnd = data['qty'] * current_p * rate
                cost_basis_vnd = data['cost_usd'] * rate if is_crypto else data['cost_usd']
                
                positions.append({
                    'ticker': ticker,
                    'qty': data['qty'],
                    'avg_price': data['cost_usd'] / data['qty'],
                    'current_price': current_p,
                    'cost': cost_basis_vnd,
                    'market_value': market_value_vnd,
                    'profit': market_value_vnd - cost_basis_vnd,
                    'roi': self.analytics.calculate_roi(cost_basis_vnd, market_value_vnd)
                })

        positions.sort(key=lambda x: x['market_value'], reverse=True)
        return {
            'positions': positions,
            'total_in': total_buy_val,
            'total_out': total_sell_val,
            'summary': self._calculate_summary(positions)
        }

    def _calculate_summary(self, positions):
        if not positions:
            return {'total_cost': 0, 'total_value': 0, 'total_profit': 0, 'total_roi': 0, 'best': None, 'worst': None, 'largest': None}
        total_cost = sum(p['cost'] for p in positions)
        total_value = sum(p['market_value'] for p in positions)
        return {
            'total_cost': total_cost,
            'total_value': total_value,
            'total_profit': total_value - total_cost,
            'total_roi': self.analytics.calculate_roi(total_cost, total_value),
            'best': max(positions, key=lambda x: x['roi']),
            'worst': min(positions, key=lambda x: x['roi']),
            'largest': max(positions, key=lambda x: x['market_value'])
        }
