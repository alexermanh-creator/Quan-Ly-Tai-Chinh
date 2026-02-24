# Cập nhật bảng transactions có thêm cột 'type'
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    asset_type TEXT,
                    type TEXT, -- BUY, SELL, IN, OUT
                    ticker TEXT,
                    amount REAL, -- Đây là Số lượng (Qty)
                    price REAL,
                    total_value REAL,
                    date TEXT,
                    note TEXT
                )
            ''')
