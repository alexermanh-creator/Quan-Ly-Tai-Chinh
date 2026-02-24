from backend.interface import BaseModule
from backend.core.portfolio_crypto import crypto_core

class Module(BaseModule):
    def get_info(self):
        return {"id": "crypto", "name": "🪙 Crypto"}

    def run(self, user_id, data=None):
        portfolio, total_vnd = crypto_core.get_portfolio(user_id)
        
        if not portfolio:
            return {
                "status": "text",
                "message": "🪙 *DANH MỤC CRYPTO*\n\nBạn chưa có đồng coin nào. Hãy dùng nút Giao dịch để thêm!",
                "buttons": ["➕ Giao dịch", "🏠 Trang chủ"]
            }

        msg = "🪙 *DANH MỤC CRYPTO (USD)*\n"
        msg += "━━━━━━━━━━━━━━━━━━━\n"
        msg += f"{'Mã':<8} | {'SL':<8} | {'Giá Vốn':<10}\n"
        
        for coin in portfolio:
            msg += f"`{coin['ticker']:<6}` | {coin['quantity']:<7.4f} | `${coin['avg_price']:,.2f}`\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💰 Tổng giá trị: `{total_vnd:,.0f}đ`\n"
        msg += "_Tỷ giá quy đổi: 1 USD = 26.300đ_"

        return {
            "status": "wizard", # Dùng wizard để hiện nút bấm
            "message": msg,
            "buttons": ["🔄 Cập nhật giá", "➕ Giao dịch", "📊 Phân bổ", "🏠 Trang chủ"]
        }
