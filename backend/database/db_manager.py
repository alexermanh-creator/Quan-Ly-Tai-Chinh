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
        """Khởi tạo các bảng dữ liệu cơ bản nếu chưa có"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Bảng lưu số dư tài sản theo loại (Stock, Crypto, Cash...)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

db = DatabaseManager()