from backend.interface import BaseModule
from backend.core.portfolio import PortfolioManager # Gọi từ manager chung

class Module(BaseModule):
    def get_info(self):
        return {"id": "crypto", "name": "🪙 Crypto"}

    def run(self, user_id, data=None):
        pm = PortfolioManager(user_id)
        # Lấy dữ liệu từ hàm get_crypto_portfolio đã chuẩn hóa
        pf = pm.get_crypto_portfolio()
        sumry = pf['summary']
        positions = pf['positions']
        
        if not positions:
            return {
                "status": "wizard",
                "message": "🪙 *DANH MỤC CRYPTO*\n\nBạn chưa có đồng coin nào. Hãy dùng lệnh: `btc 0.1 65000`!",
                "buttons": ["➕ Giao dịch", "🏠 Trang chủ"]
            }

        # Render Layout Demo Final
        msg = (
            f"🏆\n*DEMO FINAL — CRYPTO*\n"
            f"🪙\n*DANH MỤC CRYPTO*\n\n"
            f"💰 Tổng giá trị: `{sumry['total_value']:,.0f}đ`\n"
            f"💵 Tổng vốn: `{sumry['total_cost']:,.0f}đ`\n"
            f"📉 Lỗ/Lãi: `{sumry['total_profit']:,.0f}đ` ({sumry['total_roi']:+.1f}%)\n"
        )
        
        for p in positions:
            msg += (
                f"\n────────────\n\n"
                f"*{p['ticker']}*\n\n"
                f"SL: `{p['qty']}`\n\n"
                f"Giá vốn TB: `${p['avg_price']:,.2f}`\n\n"
                f"Giá trị: `{p['market_value']:,.0f}đ`\n"
            )

        return {
            "status": "wizard",
            "message": msg,
            "buttons": ["🔄 Cập nhật giá", "➕ Giao dịch", "🏠 Trang chủ"]
        }
