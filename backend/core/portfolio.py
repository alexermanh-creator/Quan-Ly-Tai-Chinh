from backend.database.db_manager import db
from backend.core.analytics import StockAnalytics

class PortfolioManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.analytics = StockAnalytics()
        self.usd_rate = 25450  # Tỷ giá có thể chuyển thành config hoặc API sau này

    def get_stock_portfolio(self):
        # Giữ nguyên logic Stock hiện tại của bạn (vì bạn nói nó đang chạy ổn)
        return self._get_asset_portfolio(asset_type='STOCK', price_table='stock_prices')

    def get_crypto_portfolio(self):
        # Tận dụng logic chung nhưng trả về dữ liệu quy đổi VND cho Crypto
        return self._get_asset_portfolio(asset_type='CRYPTO', price_table='crypto_prices', is_crypto=True)

    def _get_asset_portfolio(self, asset_type, price_table, is_crypto=False):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Lấy giá thị trường (Dùng bảng động dựa trên asset_type)
            # Crypto dùng giá USD, Stock dùng giá VND
            price_col = 'price_usd' if is_crypto else 'current_price'
            cursor.execute(f"SELECT ticker, {price_col} FROM {price_table}")
            market_prices = dict(cursor.fetchall())

            # 2. Lấy lịch sử giao dịch (Lấy thêm cột TYPE chúng ta vừa thêm vào DB)
            cursor.execute(f'''
                SELECT ticker, amount, price, total_value, type 
                FROM transactions 
                WHERE user_id = ? AND asset_type = ?
                ORDER BY date ASC
            ''', (self.user_id, asset_type))
            records = cursor.fetchall()

        portfolio = {}
        total_buy_val = 0
        total_sell_val = 0

        for ticker, amount, price, total_val, t_type in records:
            if ticker not in portfolio:
                portfolio[ticker] = {'qty': 0, 'cost': 0, 'last_price': 0}
            
            # Lưu giá giao dịch cuối làm fallback
            portfolio[ticker]['last_price'] = abs(price)
            
            # Logic xử lý theo Type (chuẩn Plug & Play)
            if t_type in ['BUY', 'IN']:
                portfolio[ticker]['qty'] += amount
                portfolio[ticker]['cost'] += abs(total_val)
                total_buy_val += abs(total_val)
            
            elif t_type in ['SELL', 'OUT']:
                if portfolio[ticker]['qty'] > 0:
                    avg_cost_per_unit = portfolio[ticker]['cost'] / portfolio[ticker]['qty']
                    portfolio[ticker]['cost'] -= abs(amount) * avg_cost_per_unit
                    portfolio[ticker]['qty'] -= abs(amount) # Đảm bảo trừ đúng số lượng
                total_sell_val += abs(total_val)

        positions = []
        rate = self.usd_rate if is_crypto else 1

        for ticker, data in portfolio.items():
            if data['qty'] > 0.000001: # Crypto cần độ chính xác cao hơn Stock
                current_p = market_prices.get(ticker, data['last_price'])
                
                # Market Value luôn quy về VND để hiển thị đồng nhất
                market_value_vnd = data['qty'] * current_p * rate
                cost_basis_vnd = data['cost'] # total_value trong DB đã là VND
                
                positions.append({
                    'ticker': ticker,
                    'qty': data['qty'],
                    'avg_price': (cost_basis_vnd / data['qty']) / rate, # Giá vốn trung bình theo USD/VND
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
        # Kế thừa hoàn toàn hàm tính toán summary của bạn
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
