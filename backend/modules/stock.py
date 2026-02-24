from backend.interface import BaseModule
from backend.core.portfolio import PortfolioManager
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "stock", "name": "📊 Cổ phiếu"}

    def format_money(self, val):
        abs_val = abs(val)
        suffix = "triệu"
        if abs_val >= 10**9:
            display_val = val / 10**9
            suffix = "tỷ"
        else:
            display_val = val / 10**6
        sign = "+" if val > 0 else ("-" if val < 0 else "")
        return f"{sign}{abs(display_val):,.1f} {suffix}"

    def run(self, user_id, data=None):
        pm = PortfolioManager(user_id)
        
        if data == "🔄 Cập nhật giá":
            return {
                "status": "wizard",
                "message": "🔄 *CẬP NHẬT GIÁ THỊ TRƯỜNG*\n\nHãy nhập: `gia [Mã] [Giá]`\n*Ví dụ:* `gia VPB 22.5`",
                "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã", "🏠 Trang chủ"]
            }

        if isinstance(data, str) and data.lower().startswith("gia "):
            try:
                parts = data.split(" ")
                ticker = parts[1].upper()
                price = float(parts[2]) * 1000
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR REPLACE INTO stock_prices (ticker, current_price) VALUES (?, ?)", (ticker, price))
                    conn.commit()
                return f"✅ Đã cập nhật giá mã *{ticker}* là `{price/1000:,.1f}k`."
            except: 
                return "⚠️ Cú pháp sai: `gia [Mã] [Giá]`"
            
        if data == "❌ Xóa mã":
            return {
                "status": "wizard",
                "message": "❌ *XÓA DỮ LIỆU MÃ*\n\nHãy nhập: `xoa [Mã]`\n*Ví dụ:* `xoa HPG`.",
                "buttons": ["📊 Cổ phiếu", "🏠 Trang chủ"]
            }

        if isinstance(data, str) and data.lower().startswith("xoa "):
            try:
                ticker_to_del = data.split(" ")[1].upper()
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM transactions WHERE user_id = ? AND ticker = ? AND asset_type = 'STOCK'", (user_id, ticker_to_del))
                    conn.commit()
                return f"✅ Đã xóa toàn bộ lịch sử mã *{ticker_to_del}*."
            except:
                return "⚠️ Lỗi khi xóa mã."

        if data == "📈 Báo cáo nhóm":
            pf_data = pm.get_stock_portfolio()
            summary = pf_data['summary']
            report = (
                f"📈 *BÁO CÁO HIỆU SUẤT*\n\n"
                f"💰 Vốn: `{self.format_money(summary['total_cost'])}`\n"
                f"💵 Hiện tại: `{self.format_money(summary['total_value'])}`\n"
                f"📊 Lãi/lỗ: *{self.format_money(summary['total_profit'])}* ({summary['total_roi']:+.2f}%)\n"
            )
            return {
                "status": "wizard",
                "message": report,
                "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã", "🏠 Trang chủ"]
            }

        # HIỂN THỊ DANH MỤC MẶC ĐỊNH
        pf_data = pm.get_stock_portfolio()
        summary = pf_data['summary']
        positions = pf_data['positions']
        
        if not positions:
            msg = "📊 *DANH MỤC CỔ PHIẾU*\n\nBạn chưa có cổ phiếu nào."
        else:
            res = (
                f"📊 *DANH MỤC CỔ PHIẾU*\n\n"
                f"💰 Giá trị: *{self.format_money(summary['total_value'])}*\n"
                f"📈 Lãi: {self.format_money(summary['total_profit'])} ({summary['total_roi']:+.1f}%)\n\n"
            )
            for p in positions:
                res += f"*{p['ticker']}*: {p['qty']:,} | Lãi: {self.format_money(p['profit'])}\n"
            msg = res

        return {
            "status": "wizard",
            "message": msg,
            "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã", "🏠 Trang chủ"]
        }
