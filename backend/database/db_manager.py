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
            
            # 1. Bảng lưu số dư tài sản (đã có)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_type TEXT UNIQUE,
                    value REAL
                )
            ''')

            # 2. Bảng lưu Lịch sử giao dịch (Bảng mới chúng ta cần)
            # Tìm từ khóa: CREATE TABLE IF NOT EXISTS transactions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    asset_type TEXT,
                    ticker TEXT,
                    amount REAL,
                    price REAL,
                    total_value REAL,
                    date TEXT,
                    note TEXT
                )
            ''')
            conn.commit()
            print("✅ Database đã được khởi tạo và cập nhật bảng Transactions.")


db = DatabaseManager()
