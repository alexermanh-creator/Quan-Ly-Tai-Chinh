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
            
        sign = "+" if val > 0 else ""
        return f"{sign}{display_val:,.1f} {suffix}"

    def run(self, user_id, data=None):
        pm = PortfolioManager(user_id)
        data = pm.get_stock_portfolio()
        summary = data['summary']
        positions = data['positions']
        
        if not positions:
            return "📊 *DANH MỤC CỔ PHIẾU*\n\nBạn chưa có cổ phiếu nào. Hãy thêm giao dịch trước!"

        # 1. Header Summary
        res = (
            f"📊 *DANH MỤC CỔ PHIẾU*\n\n"
            f"💰 Tổng giá trị:\n*{self.format_money(summary['total_value'])}*\n"
            f"💵 Tổng vốn: {self.format_money(summary['total_cost'])}\n"
            f"📈 Lãi: {self.format_money(summary['total_profit'])} ({summary['total_roi']:+.1f}%)\n\n"
            f"⬆️ Tổng nạp: {self.format_money(data['total_in'])}\n"
            f"⬇️ Tổng rút: {self.format_money(data['total_out'])}\n\n"
        )

        # 2. Key Metrics
        res += f"🏆 Mã tốt nhất:\n{summary['best']['ticker']} ({summary['best']['roi']:+.1f}%)\n"
        res += f"📉 Mã kém nhất:\n{summary['worst']['ticker']} ({summary['worst']['roi']:+.1f}%)\n"
        
        weight = (summary['largest']['market_value'] / summary['total_value'] * 100) if summary['total_value'] > 0 else 0
        res += f"📊 Tỉ trọng lớn nhất:\n{summary['largest']['ticker']} ({weight:.0f}%)\n"
        res += "────────────\n"

        # 3. Danh sách chi tiết từng mã
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

        return res
