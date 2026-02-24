from backend.interface import BaseModule
from backend.core.portfolio import PortfolioManager

class Module(BaseModule):
    def get_info(self):
        return {"id": "crypto", "name": "🪙 Crypto"}

    def format_money(self, val):
        """Định dạng tiền tệ theo chuẩn: Tỷ, Triệu hoặc đ"""
        abs_val = abs(val)
        sign = "+" if val > 0 else ("-" if val < 0 else "")
        if abs_val >= 1000000000:
            return f"{sign}{abs_val / 1000000000:,.2f} tỷ"
        elif abs_val >= 1000000:
            return f"{sign}{abs_val / 1000000:,.1f} triệu"
        return f"{sign}{abs_val:,.0f}đ"

    def run(self, user_id, data=None):
        pm = PortfolioManager(user_id)
        pf = pm.get_crypto_portfolio()
        sumry = pf['summary']
        positions = pf['positions']
        
        if not positions:
            return {
                "status": "wizard",
                "message": "🪙 *DANH MỤC CRYPTO*\n\nBạn chưa có tài sản Crypto nào.\n\n👉 *Cách nhập:* `btc 0.5 95000` (Mua 0.5 BTC giá 95k USD)",
                "buttons": ["➕ Giao dịch", "🏠 Trang chủ"]
            }

        # --- HEADER LAYOUT DEMO FINAL ---
        msg = (
            f"🏆\n*DEMO FINAL — CRYPTO*\n"
            f"🪙\n*DANH MỤC CRYPTO*\n\n"
            f"💰 Tổng giá trị:\n*{self.format_money(sumry['total_value'])}*\n\n"
            f"💵 Tổng vốn: {self.format_money(sumry['total_cost'])}\n"
            f"📉 Lỗ/Lãi: {self.format_money(sumry['total_profit'])} ({sumry['total_roi']:+.1f}%)\n\n"
            f"⬆️ Tổng nạp: {self.format_money(pf['total_in'])}\n"
            f"⬇️ Tổng rút: {self.format_money(pf['total_out'])}\n"
        )

        # --- PHẦN PHÂN TÍCH NHÓM ---
        if sumry.get('best'):
            best = sumry['best']
            worst = sumry['worst']
            largest = sumry['largest']
            
            # Tính tỷ trọng cho đồng lớn nhất
            weight = (largest['market_value'] / sumry['total_value'] * 100) if sumry['total_value'] > 0 else 0
            
            msg += (
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 Coin tốt nhất: {best['ticker']} ({best['roi']:+.1f}%)\n"
                f"📉 Coin kém nhất: {worst['ticker']} ({worst['roi']:+.1f}%)\n"
                f"📊 Tỉ trọng lớn nhất: {largest['ticker']} ({weight:.1f}%)\n"
            )

        # --- CHI TIẾT TỪNG COIN (CÓ ĐƯỜNG KẺ) ---
        for p in positions:
            msg += (
                f"\n────────────\n\n"
                f"*{p['ticker']}*\n\n"
                f"SL: `{p['qty']}`\n\n"
                f"Giá vốn TB: `${p['avg_price']:,.1f}`\n\n"
                f"Giá hiện tại: `${p['current_price']:,.1f}`\n\n"
                f"Giá trị: {self.format_money(p['market_value'])}\n\n"
                f"Lãi: {self.format_money(p['profit'])} ({p['roi']:+.1f}%)\n"
            )

        return {
            "status": "wizard",
            "message": msg + "\n\n📱 *MENU CRYPTO*",
            "buttons": ["🔄 Cập nhật giá", "➕ Giao dịch", "📈 Báo cáo", "🏠 Trang chủ"]
        }
