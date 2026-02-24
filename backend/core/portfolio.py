from backend.database.db_manager import db
from backend.core.analytics import StockAnalytics

class PortfolioManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.analytics = StockAnalytics()

    def get_stock_portfolio(self):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # Lấy toàn bộ lịch sử giao dịch STOCK, sắp xếp theo thời gian
            cursor.execute('''
                SELECT ticker, amount, price, total_value 
                FROM transactions 
                WHERE user_id = ? AND asset_type = 'STOCK'
                ORDER BY date ASC
            ''', (self.user_id,))
            records = cursor.fetchall()

        portfolio = {}
        total_buy_val = 0  # Tổng tiền đã bỏ ra mua (Tổng nạp nhóm)
        total_sell_val = 0 # Tổng tiền đã thu về khi bán (Tổng rút nhóm)

        for ticker, amount, price, total_val in records:
            if ticker not in portfolio:
                portfolio[ticker] = {'qty': 0, 'cost': 0, 'last_price': 0}
            
            # Cập nhật giá gần nhất (giả lập giá hiện tại)
            portfolio[ticker]['last_price'] = abs(price)
            
            if amount > 0: # LỆNH MUA
                portfolio[ticker]['qty'] += amount
                portfolio[ticker]['cost'] += abs(total_val)
                total_buy_val += abs(total_val)
            
            elif amount < 0: # LỆNH BÁN
                # Trước khi trừ, tính giá vốn TB của 1 cổ phiếu
                if portfolio[ticker]['qty'] > 0:
                    avg_cost_per_unit = portfolio[ticker]['cost'] / portfolio[ticker]['qty']
                    # Trừ bớt giá vốn tương ứng với số lượng bán ra
                    portfolio[ticker]['cost'] -= abs(amount) * avg_cost_per_unit
                    portfolio[ticker]['qty'] += amount # amount âm nên sẽ giảm qty
                
                total_sell_val += abs(total_val)

        positions = []
        for ticker, data in portfolio.items():
            # Chỉ hiển thị những mã còn số dư trong kho
            if data['qty'] > 0.001: 
                market_value = data['qty'] * data['last_price']
                cost_basis = data['cost']
                profit = market_value - cost_basis
                
                positions.append({
                    'ticker': ticker,
                    'qty': data['qty'],
                    'avg_price': cost_basis / data['qty'],
                    'current_price': data['last_price'],
                    'cost': cost_basis,
                    'market_value': market_value,
                    'profit': profit,
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
