from backend.database.db_manager import db
from backend.core.analytics import StockAnalytics

class PortfolioManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.analytics = StockAnalytics()

    def get_stock_portfolio(self):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Khởi tạo bảng lưu giá thị trường nếu chưa có
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_prices (
                    ticker TEXT PRIMARY KEY,
                    current_price REAL
                )
            ''')
            
            # 2. Lấy từ bảng giá thị trường (những giá do người dùng cập nhật thủ công)
            cursor.execute("SELECT ticker, current_price FROM stock_prices")
            market_prices = dict(cursor.fetchall())

            # 3. Lấy toàn bộ lịch sử giao dịch STOCK của User
            cursor.execute('''
                SELECT ticker, amount, price, total_value 
                FROM transactions 
                WHERE user_id = ? AND asset_type = 'STOCK'
                ORDER BY date ASC
            ''', (self.user_id,))
            records = cursor.fetchall()

        portfolio = {}
        total_buy_val = 0  # Tổng nạp nhóm
        total_sell_val = 0 # Tổng rút nhóm

        for ticker, amount, price, total_val in records:
            if ticker not in portfolio:
                portfolio[ticker] = {'qty': 0, 'cost': 0, 'last_price': 0}
            
            # Lưu giá giao dịch cuối cùng làm phương án dự phòng (fallback)
            portfolio[ticker]['last_price'] = abs(price)
            
            if amount > 0: # LỆNH MUA
                portfolio[ticker]['qty'] += amount
                portfolio[ticker]['cost'] += abs(total_val)
                total_buy_val += abs(total_val)
            
            elif amount < 0: # LỆNH BÁN
                if portfolio[ticker]['qty'] > 0:
                    # Tính giá vốn TB để trừ vốn theo tỷ lệ
                    avg_cost_per_unit = portfolio[ticker]['cost'] / portfolio[ticker]['qty']
                    portfolio[ticker]['cost'] -= abs(amount) * avg_cost_per_unit
                    portfolio[ticker]['qty'] += amount 
                
                total_sell_val += abs(total_val)

        positions = []
        for ticker, data in portfolio.items():
            if data['qty'] > 0.001: 
                # ƯU TIÊN: Lấy giá từ bảng stock_prices, nếu không có thì lấy giá giao dịch cuối
                current_p = market_prices.get(ticker, data['last_price'])
                
                market_value = data['qty'] * current_p
                cost_basis = data['cost']
                
                positions.append({
                    'ticker': ticker,
                    'qty': data['qty'],
                    'avg_price': cost_basis / data['qty'],
                    'current_price': current_p,
                    'cost': cost_basis,
                    'market_value': market_value,
                    'profit': market_value - cost_basis,
                    'roi': self.analytics.calculate_roi(cost_basis, market_value)
                })

        # Sắp xếp danh mục theo giá trị thị trường giảm dần
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
