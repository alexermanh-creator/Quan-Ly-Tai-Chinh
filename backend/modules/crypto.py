from backend.interface import BaseModule
from backend.core.portfolio import PortfolioManager

class Module(BaseModule):
    def get_info(self):
        return {"id": "crypto", "name": "🪙 Crypto"}

    def format_money(self, val):
        abs_val = abs(val)
        sign = "+" if val > 0 else ("-" if val < 0 else "")
        if abs_val >= 1000000000: return f"{sign}{abs_val/1000000000:,.2f} tỷ"
        if abs_val >= 1000000: return f"{sign}{abs_val/1000000:,.1f} triệu"
        return f"{sign}{abs_val:,.0f}đ"

    def run(self, user_id, data=None):
        pm = PortfolioManager(user_id)
        pf = pm.get_crypto_portfolio()
        s = pf['summary']
        positions = pf['positions']
        
        if not positions:
            return {
                "status": "wizard",
                "message": "🪙 *DANH MỤC CRYPTO*\n\nBạn chưa có tài sản nào. Gõ lệnh: `btc 0.1 95000`",
                "buttons": ["➕ Giao dịch", "🏠 Trang chủ"]
            }

        # --- HEADER FULL LAYOUT ---
        msg = (
            f"🏆\n*DEMO FINAL — CRYPTO*\n"
            f"🪙\n*DANH MỤC CRYPTO*\n\n"
            f"💰 Tổng giá trị:\n*{self.format_money(s['total_value'])}*\n\n"
            f"💵 Tổng vốn: {self.format_money(s['total_cost'])}\n"
            f"📉 Lỗ/Lãi: {self.format_money(s['total_profit'])} ({s['total_roi']:+.1f}%)\n\n"
            f"⬆️ Tổng nạp: {self.format_money(pf['total_in'])}\n"
            f"⬇️ Tổng rút: {self.format_money(pf['total_out'])}\n"
        )

        if s.get('best'):
            weight = (s['largest']['market_value'] / s['total_value'] * 100) if s['total_value'] > 0 else 0
            msg += (
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 Coin tốt nhất: {s['best']['ticker']} ({s['best']['roi']:+.1f}%)\n"
                f"📉 Coin kém nhất: {s['worst']['ticker']} ({s['worst']['roi']:+.1f}%)\n"
                f"📊 Tỉ trọng lớn nhất: {s['largest']['ticker']} ({weight:.1f}%)\n"
            )

        for p in positions:
            msg += (
                f"\n────────────\n\n"
                f"*{p['ticker']}*\n\n"
                f"SL: `{p['qty']}`\n\n"
                f"Giá vốn TB: `${p['avg_price']:,.1f}`\n\n"
                f"Giá trị: {self.format_money(p['market_value'])}\n\n"
                f"Lãi: {self.format_money(p['profit'])} ({p['roi']:+.1f}%)\n"
            )

        return {"status": "wizard", "message": msg, "buttons": ["➕ Giao dịch", "🏠 Trang chủ"]}
