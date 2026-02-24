import sqlite3
import os

class DatabaseManager:
    def __init__(self):
        # Đảm bảo thư mục database tồn tại
        db_dir = os.path.dirname(__file__)
        self.db_path = os.path.join(db_dir, "finance.db")
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Bảng lưu số dư tài sản (Tổng hợp)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_type TEXT UNIQUE,
                    value REAL
                )
            ''')

            # 2. Bảng Lịch sử giao dịch (Đã bổ sung cột TYPE)
            # amount: Số lượng (Qty) | total_value: Tổng tiền (VNĐ hoặc quy đổi)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    asset_type TEXT, -- STOCK, CRYPTO, CASH, OTHER
                    type TEXT,       -- BUY, SELL, IN, OUT
                    ticker TEXT,     -- VNM, BTC, ETH...
                    amount REAL,     -- Số lượng
                    price REAL,      -- Giá khớp (USD cho Crypto, VNĐ cho Stock)
                    total_value REAL, -- Tổng giá trị quy đổi VNĐ
                    date TEXT,
                    note TEXT
                )
            ''')

            # 3. Bảng lưu giá Crypto (Phục vụ module Crypto)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crypto_prices (
                    symbol TEXT PRIMARY KEY,
                    price_usd REAL,
                    last_update TEXT
                )
            ''')

            # 4. Bảng lưu giá Stock (Phục vụ module Stock)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_prices (
                    ticker TEXT PRIMARY KEY,
                    current_price REAL,
                    last_update TEXT
                )
            ''')

            conn.commit()
            print("✅ Database đã được khởi tạo chuẩn hóa cho Multi-Module.")

db = DatabaseManager()
