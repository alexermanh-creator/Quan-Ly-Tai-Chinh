from backend.interface import BaseModule
from backend.core.portfolio import PortfolioManager

class Module(BaseModule):
    def get_info(self):
        return {"id": "stock", "name": "📊 Cổ phiếu"}

    def format_money(self, val):
        if abs(val) >= 10**9: return f"{val/10**9:,.2f} tỷ"
        return f"{val/10**6:,.1f} triệu"

    def run(self, user_id, data=None):
        pm = PortfolioManager(user_id)
        data = pm.get_stock_portfolio()
        summary = data['summary']
        
        # 1. Header Summary
        res = (
            f"📊 *DANH MỤC CỔ PHIẾU*\n\n"
            f"💰 Tổng giá trị: `{self.format_money(summary['total_value'])}`\n"
            f"💵 Tổng vốn: {self.format_money(summary['total_cost'])}\n"
            f"📈 Lãi: {self.format_money(summary['total_profit'])} ({summary['total_roi']:.1f}%)\n\n"
            f"⬆️ Tổng nạp: {self.format_money(data['total_in'])}\n"
            f"⬇️ Tổng rút: {self.format_money(data['total_out'])}\n\n"
        )

        # 2. Key Metrics
        if summary['best']:
            res += f"🏆 Mã tốt nhất: {summary['best']['ticker']} (+{summary['best']['roi']:.1f}%)\n"
            res += f"📉 Mã kém nhất: {summary['worst']['ticker']} ({summary['worst']['roi']:.1f}%)\n"
            res += f"📊 Tỉ trọng lớn nhất: {summary['largest']['ticker']}\n"
            res += "────────────\n"

        # 3. Danh sách chi tiết từng mã
        for p in data['positions']:
            res += (
                f"\n🔹 *{p['ticker']}*\n"
                f"▫️ SL: `{p['qty']:,}` | Vốn TB: `{p['avg_price']/1000:,.1f}k`\n"
                f"▫️ Giá hiện tại: `{p['current_price']/1000:,.1f}k`\n"
                f"▫️ Giá trị: {self.format_money(p['market_value'])}\n"
                f"▫️ Lãi: {self.format_money(p['profit'])} ({p['roi']:.1f}%)\n"
                f"────────────"
            )

        return res
