from backend.interface import BaseModule
from backend.core.portfolio import PortfolioManager
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "crypto", "name": "🪙 Crypto"}

    def can_handle(self, text):
        """Tự nhận diện các lệnh điều khiển riêng của Crypto"""
        btns = ["🪙 Crypto", "🔄 Cập nhật giá Crypto", "📈 Báo cáo nhóm Crypto", "❌ Xóa coin"]
        return text in btns or text.lower().startswith(("price ", "del "))

    def format_money(self, val):
        """Định dạng tiền tệ VNĐ (Triệu/Tỷ) theo đề bài"""
        abs_val = abs(val)
        if abs_val >= 10**9:
            display_val = val / 10**9
            suffix = "tỷ"
        else:
            display_val = val / 10**6
            suffix = "triệu"
        
        # Định dạng dấu +/-
        sign = "+" if val > 0 else ("-" if val < 0 else "")
        return f"{sign}{abs(display_val):,.1f} {suffix}"

    def run(self, user_id, data=None):
        pm = PortfolioManager(user_id)
        
        # 1. XỬ LÝ LỆNH CẬP NHẬT GIÁ NHANH (VD: price btc 68000)
        if isinstance(data, str) and data.lower().startswith("price "):
            try:
                parts = data.split()
                symbol = parts[1].upper()
                price_usd = float(parts[2])
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO crypto_prices (symbol, price_usd, last_update) 
                        VALUES (?, ?, datetime('now'))
                    """, (symbol, price_usd))
                    conn.commit()
                return f"✅ Đã cập nhật giá *{symbol}* là `${price_usd:,.0f}`"
            except:
                return "⚠️ Cú pháp sai. VD: `price BTC 68000`"

        # 2. XỬ LÝ LỆNH XÓA COIN (Lệnh nguy hiểm)
        if isinstance(data, str) and data.lower().startswith("del "):
            try:
                symbol = data.split()[1].upper()
                with db.get_connection() as conn:
                    conn.execute("DELETE FROM transactions WHERE user_id = ? AND ticker = ? AND asset_type = 'CRYPTO'", (user_id, symbol))
                    conn.commit()
                return f"❌ Đã xóa toàn bộ dữ liệu của đồng *{symbol}*."
            except:
                return "⚠️ Cú pháp sai. VD: `del SOL`"

        # 3. HIỂN THỊ LAYOUT DANH MỤC (DEMO FINAL)
        pf = pm.get_crypto_portfolio()
        sumry = pf['summary']
        positions = pf['positions']

        if not positions:
            msg = "🪙 *DANH MỤC CRYPTO*\n\nBạn chưa có tài sản Crypto nào. Hãy dùng lệnh: `btc 0.1 65000` để bắt đầu."
        else:
            # Header theo đúng Layout Demo
            res = (
                f"🏆\n*DEMO FINAL — CRYPTO*\n"
                f"🪙\n*DANH MỤC CRYPTO*\n\n"
                f"💰 Tổng giá trị:\n*{self.format_money(sumry['total_value'])}*\n"
                f"💵 Tổng vốn: {self.format_money(sumry['total_cost'])}\n"
                f"📉 Lỗ/Lãi: {self.format_money(sumry['total_profit'])} ({sumry['total_roi']:+.1f}%)\n\n"
                f"⬆️ Tổng nạp: {self.format_money(pf['total_in'])}\n"
                f"⬇️ Tổng rút: {self.format_money(pf['total_out'])}\n\n"
            )

            # Phân tích tốt nhất/kém nhất
            if sumry['best']:
                res += f"🏆 Coin tốt nhất:\n{sumry['best']['ticker']} ({sumry['best']['roi']:+.1f}%)\n"
                res += f"📉 Coin kém nhất:\n{sumry['worst']['ticker']} ({sumry['worst']['roi']:+.1f}%)\n"
                
                # Tính tỉ trọng
                largest = sumry['largest']
                weight = (largest['market_value'] / sumry['total_value']) * 100 if sumry['total_value'] > 0 else 0
                res += f"📊 Tỉ trọng lớn nhất:\n{largest['ticker']} ({weight:.1f}%)\n"

            # Chi tiết từng Coin với đường gạch ngang
            for p in positions:
                res += (
                    f"\n────────────\n\n"
                    f"*{p['ticker']}*\n\n"
                    f"SL: `{p['qty']}`\n\n"
                    f"Giá vốn TB: `{p['avg_price']:,.0f}`\n\n"
                    f"Giá hiện tại: `{p['current_price']:,.0f}`\n\n"
                    f"Giá trị: {self.format_money(p['market_value'])}\n\n"
                    f"Lãi: {self.format_money(p['profit'])} ({p['roi']:+.1f}%)\n"
                )
            msg = res

        return {
            "status": "wizard",
            "message": msg + "\n\n📱\n*MENU CRYPTO MODULE*",
            "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá Crypto", "📈 Báo cáo nhóm Crypto", "❌ Xóa coin", "🏠 Trang chủ"]
        }
