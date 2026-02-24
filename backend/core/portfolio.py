from backend.database.db_manager import db
from backend.core.analytics import StockAnalytics

class PortfolioManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.analytics = StockAnalytics()
        self.usd_rate = 25450  # Tỷ giá chuẩn

    def get_stock_portfolio(self):
        return self._get_asset_portfolio(asset_type='STOCK', price_table='stock_prices')

    def get_crypto_portfolio(self):
        return self._get_asset_portfolio(asset_type='CRYPTO', price_table='crypto_prices', is_crypto=True)

    def _get_asset_portfolio(self, asset_type, price_table, is_crypto=False):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Lấy giá thị trường (Dùng UPPER để tránh lỗi đồng nhất mã)
            price_col = 'price_usd' if is_crypto else 'current_price'
            cursor.execute(f"SELECT UPPER(ticker), {price_col} FROM {price_table}")
            market_prices = {row[0]: row[1] for row in cursor.fetchall()}

            # 2. Lấy lịch sử giao dịch (Sửa lỗi: Dùng UPPER(asset_type) để lọc chính xác)
            cursor.execute(f'''
                SELECT UPPER(ticker), amount, price, total_value, UPPER(type) 
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
                portfolio[ticker] = {'qty': 0, 'cost': 0, 'last_price': 0}
            
            portfolio[ticker]['last_price'] = abs(price)
            
            # Logic tính toán dựa trên TYPE (BUY/IN vs SELL/OUT)
            if t_type in ['BUY', 'IN']:
                portfolio[ticker]['qty'] += abs(amount)
                portfolio[ticker]['cost'] += abs(total_val)
                total_buy_val += abs(total_val)
            
            elif t_type in ['SELL', 'OUT']:
                if portfolio[ticker]['qty'] > 0:
                    # Trình tự: Tính giá vốn trung bình trước khi trừ số lượng
                    avg_cost_per_unit = portfolio[ticker]['cost'] / portfolio[ticker]['qty']
                    portfolio[ticker]['cost'] -= abs(amount) * avg_cost_per_unit
                    portfolio[ticker]['qty'] -= abs(amount)
                total_sell_val += abs(total_val)

        positions = []
        rate = self.usd_rate if is_crypto else 1

        for ticker, data in portfolio.items():
            # Điều kiện hiển thị: Số lượng phải lớn hơn 0
            if data['qty'] > 0.00000001: 
                current_p = market_prices.get(ticker, data['last_price'])
                
                market_value_vnd = data['qty'] * current_p * rate
                cost_basis_vnd = data['cost'] 
                
                positions.append({
                    'ticker': ticker,
                    'qty': data['qty'],
                    'avg_price': (cost_basis_vnd / data['qty']) / rate if data['qty'] > 0 else 0,
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
            return {
                'total_cost': 0, 'total_value': 0, 'total_profit': 0, 
                'total_roi': 0, 'best': None, 'worst': None, 'largest': None
            }

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
