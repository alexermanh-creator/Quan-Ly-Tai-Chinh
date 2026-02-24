from backend.interface import BaseModule
from backend.core.portfolio import PortfolioManager
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "stock", "name": "📊 Cổ phiếu"}

    def can_handle(self, text):
        """Hàm quan trọng: Giúp bot_client chuyển hướng tin nhắn vào đây"""
        btns = ["📊 Cổ phiếu", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã"]
        return text in btns or text.lower().startswith(("gia ", "xoa "))

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
        
        # --- 1. XỬ LÝ LỆNH TỪ MENU CON ---
        if data == "🔄 Cập nhật giá":
            return {
                "status": "wizard",
                "message": "🔄 *CẬP NHẬT GIÁ THỊ TRƯỜNG*\n\nHãy nhập theo cú pháp: `gia [Mã] [Giá]`\n(Đơn vị là nghìn đồng)\n\n*Ví dụ:* `gia VPB 22.5` (tương ứng 22,500đ)",
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
                return f"✅ Đã cập nhật giá thị trường mã *{ticker}* là `{price/1000:,.1f}k`. Bấm [📊 Cổ phiếu] để xem thay đổi."
            except: 
                return "⚠️ Cú pháp sai. Hãy nhập: `gia [Mã] [Giá]`"
            
        if data == "❌ Xóa mã":
            return {
                "status": "wizard",
                "message": "❌ *XÓA DỮ LIỆU MÃ*\n\nĐể xóa toàn bộ lịch sử giao dịch của một mã, hãy nhập lệnh:\n`xoa [Mã]`\n\n*Ví dụ:* `xoa HPG`",
                "buttons": ["📊 Cổ phiếu", "🏠 Trang chủ"]
            }

        if isinstance(data, str) and data.lower().startswith("xoa "):
            try:
                ticker_to_del = data.split(" ")[1].upper()
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM transactions WHERE user_id = ? AND ticker = ? AND asset_type = 'STOCK'", (user_id, ticker_to_del))
                    conn.commit()
                return f"✅ Đã xóa toàn bộ lịch sử giao dịch mã *{ticker_to_del}*."
            except Exception as e:
                return f"⚠️ Lỗi khi xóa: {str(e)}"

        if data == "📈 Báo cáo nhóm":
            pf_data = pm.get_stock_portfolio()
            summary = pf_data['summary']
            if not pf_data['positions']:
                return "⚠️ Bạn chưa có dữ liệu để lập báo cáo."
                
            report = (
                f"📈 *BÁO CÁO HIỆU SUẤT CỔ PHIẾU*\n\n"
                f"💰 Tổng vốn ròng: `{self.format_money(summary['total_cost'])}`\n"
                f"💵 Giá trị hiện tại: `{self.format_money(summary['total_value'])}`\n"
                f"📊 Tổng lãi/lỗ: *{self.format_money(summary['total_profit'])}*\n"
                f"🚀 Tỷ suất (ROI): `{summary['total_roi']:+.2f}%`\n\n"
                f"⬆️ Tổng tiền nạp: {self.format_money(pf_data['total_in'])}\n"
                f"⬇️ Tổng tiền rút: {self.format_money(pf_data['total_out'])}\n\n"
                f"🔥 *Đánh giá:* " + ("Danh mục đang tăng trưởng tốt!" if summary['total_roi'] > 0 else "Cần rà soát lại các mã yếu kém.")
            )
            return {
                "status": "wizard",
                "message": report,
                "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã", "🏠 Trang chủ"]
            }

        # --- 2. HIỂN THỊ DANH MỤC (LAYOUT GỐC CỦA BẠN) ---
        pf_data = pm.get_stock_portfolio()
        summary = pf_data['summary']
        positions = pf_data['positions']
        
        if not positions:
            msg = "📊 *DANH MỤC CỔ PHIẾU*\n\nBạn chưa có cổ phiếu nào trong danh mục."
        else:
            res = (
                f"📊 *DANH MỤC CỔ PHIẾU*\n\n"
                f"💰 Tổng giá trị:\n*{self.format_money(summary['total_value'])}*\n"
                f"💵 Tổng vốn: {self.format_money(summary['total_cost'])}\n"
                f"📈 Lãi: {self.format_money(summary['total_profit'])} ({summary['total_roi']:+.1f}%)\n\n"
                f"⬆️ Tổng nạp: {self.format_money(pf_data['total_in'])}\n"
                f"⬇️ Tổng rút: {self.format_money(pf_data['total_out'])}\n\n"
            )

            if summary.get('best'):
                res += f"🏆 Mã tốt nhất: {summary['best']['ticker']} ({summary['best']['roi']:+.1f}%)\n"
                res += f"📉 Mã kém nhất: {summary['worst']['ticker']} ({summary['worst']['roi']:+.1f}%)\n"
                weight = (summary['largest']['market_value'] / summary['total_value'] * 100) if summary['total_value'] > 0 else 0
                res += f"📊 Tỉ trọng lớn nhất: {summary['largest']['ticker']} ({weight:.0f}%)\n"
                res += "────────────\n"

            for p in positions:
                res += (
                    f"\n*{p['ticker']}*\n"
                    f"SL: `{p['qty']:,}`\n"
                    f"Giá vốn TB: `{p['avg_price']/1000:,.1f}k`\n"
                    f"Giá hiện tại: `{p['current_price']/1000:,.1f}k`\n"
                    f"Giá trị: {self.format_money(p['market_value'])}\n"
                    f"Lãi: {self.format_money(p['profit'])} ({p['roi']:+.1f}%)\n"
                    f"────────────"
                )
            msg = res

        return {
            "status": "wizard",
            "message": msg,
            "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã", "🏠 Trang chủ"]
        }
