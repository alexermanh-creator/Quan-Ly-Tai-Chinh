from backend.database.db_manager import db

class PortfolioCrypto:
    def __init__(self, exchange_rate_usd=26300):
        self.exchange_rate = exchange_rate_usd

    def get_portfolio(self, user_id):
        """Tính toán chi tiết danh mục Crypto"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # Lấy tất cả giao dịch Crypto của user
            cursor.execute('''
                SELECT ticker, amount, price, total_value 
                FROM transactions 
                WHERE user_id = ? AND asset_type = 'CRYPTO'
                ORDER BY date ASC
            ''', (user_id,))
            transactions = cursor.fetchall()

        portfolio = {}
        for ticker, amount, price, total_value in transactions:
            if ticker not in portfolio:
                portfolio[ticker] = {'quantity': 0.0, 'total_cost_usd': 0.0}
            
            # Tính số dư và giá vốn (USD)
            portfolio[ticker]['quantity'] += amount
            if amount > 0: # Lệnh mua
                portfolio[ticker]['total_cost_usd'] += total_value
            elif portfolio[ticker]['quantity'] < 0.00000001: # Đã bán hết
                portfolio[ticker]['total_cost_usd'] = 0.0

        # Lọc bỏ những đồng đã bán sạch (SL = 0)
        active_portfolio = []
        total_value_vnd = 0
        
        for ticker, data in portfolio.items():
            if data['quantity'] > 0:
                avg_price = data['total_cost_usd'] / data['quantity'] if data['quantity'] > 0 else 0
                
                # Giả lập giá hiện tại bằng giá vốn (Bạn sẽ update giá thủ công hoặc API sau)
                current_price = avg_price 
                current_value_usd = data['quantity'] * current_price
                
                active_portfolio.append({
                    'ticker': ticker,
                    'quantity': data['quantity'],
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'value_usd': current_value_usd,
                    'profit_pct': 0.0 # Tạm thời bằng 0 cho tới khi cập nhật giá
                })
                total_value_vnd += current_value_usd * self.exchange_rate
                
        return active_portfolio, total_value_vnd

# Khởi tạo instance dùng chung
crypto_core = PortfolioCrypto()
