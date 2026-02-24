from backend.interface import BaseModule
from backend.core.portfolio import PortfolioManager

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
        
        # --- XỬ LÝ CÁC LỆNH TỪ MENU CON ---
        if data == "🔄 Cập nhật giá":
            # Tạm thời trả về thông báo, chúng ta sẽ viết logic này ở bước tiếp theo
            return {
                "status": "wizard",
                "message": "🔄 *TÍNH NĂNG ĐANG PHÁT TRIỂN*\n\nBạn sẽ sớm có thể cập nhật giá thị trường trực tiếp tại đây.",
                "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã", "⬅️ Back"]
            }
            
        if data == "❌ Xóa mã":
            return {
                "status": "wizard",
                "message": "❌ *XÓA MÃ*\n\nBạn muốn xóa lịch sử giao dịch của mã nào? (Vui lòng nhập mã, VD: HPG)",
                "buttons": ["⬅️ Back"]
            }

        # --- HIỂN THỊ DANH MỤC (DEFAULT FLOW) ---
        pf_data = pm.get_stock_portfolio()
        summary = pf_data['summary']
        positions = pf_data['positions']
        
        if not positions:
            msg = "📊 *DANH MỤC CỔ PHIẾU*\n\nBạn chưa có cổ phiếu nào trong danh mục. Hãy thực hiện giao dịch mua đầu tiên!"
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
                res += f"🏆 Mã tốt nhất:\n{summary['best']['ticker']} ({summary['best']['roi']:+.1f}%)\n"
                res += f"📉 Mã kém nhất:\n{summary['worst']['ticker']} ({summary['worst']['roi']:+.1f}%)\n"
                
                weight = (summary['largest']['market_value'] / summary['total_value'] * 100) if summary['total_value'] > 0 else 0
                res += f"📊 Tỉ trọng lớn nhất:\n{summary['largest']['ticker']} ({weight:.0f}%)\n"
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

        # Trả về kết quả dưới dạng Wizard để hiện Menu con
        return {
            "status": "wizard",
            "message": msg,
            "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã", "⬅️ Back"]
        }
