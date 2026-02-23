from backend.interface import BaseModule
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "transaction", "name": "➕ Nhập giao dịch"}

    def run(self, user_id, data=None):
        if not data: return "Nhập: [Tên tài sản] [Số tiền]. Ví dụ: `CASH 500000`"
        try:
            name, amount = data.split()[0].upper(), float(data.split()[1])
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM assets WHERE asset_type=?", (name,))
                row = cursor.fetchone()
                if row: cursor.execute("UPDATE assets SET value=? WHERE asset_type=?", (row[0]+amount, name))
                else: cursor.execute("INSERT INTO assets (asset_type, value) VALUES (?,?)", (name, amount))
                conn.commit()
            return f"✅ Đã ghi nhận {name}: +{amount:,.0f} VNĐ"
        except: return "❌ Sai cú pháp. Thử lại: `BANK 2000000`"
