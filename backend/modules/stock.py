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
        
        # --- 1. XỬ LÝ LỆNH TỪ MENU CON ---
        
        # Phản hồi khi nhấn nút Cập nhật giá
        if data == "🔄 Cập nhật giá":
            return {
                "status": "wizard",
                "message": "🔄 *CẬP NHẬT GIÁ THỊ TRƯỜNG*\n\nHệ thống sẽ tự động cập nhật trong bản nâng cấp tới. Hiện tại bạn có thể cập nhật thủ công bằng cách nhập giao dịch Mua/Bán với giá mới nhất.",
                "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã", "⬅️ Back"]
            }
            
        # Phản hồi khi nhấn nút Xóa mã
        if data == "❌ Xóa mã":
            return {
                "status": "wizard",
                "message": "❌ *XÓA DỮ LIỆU MÃ*\n\nĐể xóa toàn bộ lịch sử giao dịch của một mã (để làm sạch danh mục), hãy nhập lệnh:\n`xoa [Mã]`\n\n*Ví dụ:* `xoa HPG`",
                "buttons": ["⬅️ Back"]
            }

        # Xử lý logic xóa mã khi người dùng nhập "xoa HPG"
        if isinstance(data, str) and data.lower().startswith("xoa "):
            ticker_to_del = data.split(" ")[1].upper()
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM transactions WHERE user_id = ? AND ticker = ? AND asset_type = 'STOCK'", 
                                 (user_id, ticker_to_del))
                    conn.commit()
                return f"✅ Đã xóa toàn bộ lịch sử giao dịch mã *{ticker_to_del}*. Bấm [📊 Cổ phiếu] để cập nhật lại danh mục."
            except Exception as e:
                return f"⚠️ Lỗi khi xóa: {str(e)}"

        # --- 2. HIỂN THỊ DANH MỤC (DEFAULT FLOW) ---
        pf_data = pm.get_stock_portfolio()
        summary = pf_data['summary']
        positions = pf_data['positions']
        
        if not positions:
            msg = "📊 *DANH MỤC CỔ PHIẾU*\n\nBạn chưa có cổ phiếu nào trong danh mục. Hãy thực hiện giao dịch mua đầu tiên bằng nút bấm bên dưới!"
        else:
            # 1. Header Summary
            res = (
                f"📊 *DANH MỤC CỔ PHIẾU*\n\n"
                f"💰 Tổng giá trị:\n*{self.format_money(summary['total_value'])}*\n"
                f"💵 Tổng vốn: {self.format_money(summary['total_cost'])}\n"
                f"📈 Lãi: {self.format_money(summary['total_profit'])} ({summary['total_roi']:+.1f}%)\n\n"
                f"⬆️ Tổng nạp: {self.format_money(pf_data['total_in'])}\n"
                f"⬇️ Tổng rút: {self.format_money(pf_data['total_out'])}\n\n"
            )

            # 2. Key Metrics
            if summary['best']:
                res += f"🏆 Mã tốt nhất: {summary['best']['ticker']} ({summary['best']['roi']:+.1f}%)\n"
                res += f"📉 Mã kém nhất: {summary['worst']['ticker']} ({summary['worst']['roi']:+.1f}%)\n"
                
                weight = (summary['largest']['market_value'] / summary['total_value'] * 100) if summary['total_value'] > 0 else 0
                res += f"📊 Tỉ trọng lớn nhất: {summary['largest']['ticker']} ({weight:.0f}%)\n"
                res += "────────────\n"

            # 3. Danh sách chi tiết từng mã (Layout Dọc)
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

        # Trả về kết quả dưới dạng Wizard để hiện Menu con chuyên biệt
        return {
            "status": "wizard",
            "message": msg,
            "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã", "⬅️ Back"]
        }
