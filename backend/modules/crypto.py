from backend.interface import BaseModule
from backend.core.portfolio import PortfolioManager
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "crypto", "name": "🪙 Crypto"}

    def can_handle(self, text):
        """Đồng bộ tập lệnh dùng chung với Stock: gia, xoa"""
        btns = ["🪙 Crypto", "🔄 Cập nhật giá", "📈 Báo cáo", "❌ Xóa mã"]
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
        
        # --- 1. XỬ LÝ LỆNH MENU CON (ĐỒNG BỘ STOCK) ---
        
        # Cập nhật giá
        if data == "🔄 Cập nhật giá":
            return {
                "status": "wizard",
                "message": "🔄 *CẬP NHẬT GIÁ CRYPTO*\n\nHãy nhập theo cú pháp: `gia [Mã] [Giá_USD]`\n\n*Ví dụ:* `gia BTC 65000`",
                "buttons": ["➕ Giao dịch", "📈 Báo cáo", "❌ Xóa mã", "🏠 Trang chủ"]
            }

        if isinstance(data, str) and data.lower().startswith("gia "):
            try:
                parts = data.split(" ")
                ticker = parts[1].upper()
                price = float(parts[2])
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    # Cập nhật vào bảng crypto_prices (dùng symbol)
                    cursor.execute("INSERT OR REPLACE INTO crypto_prices (symbol, price_usd) VALUES (?, ?)", (ticker, price))
                    conn.commit()
                return f"✅ Đã cập nhật giá *{ticker}* là `${price:,.1f}`. Bấm [🪙 Crypto] để thấy thay đổi."
            except:
                return "⚠️ Cú pháp sai. Hãy nhập: `gia [Mã] [Giá_USD]`"

        # Xóa mã
        if data == "❌ Xóa mã":
            return {
                "status": "wizard",
                "message": "❌ *XÓA DỮ LIỆU COIN*\n\nĐể xóa toàn bộ lịch sử giao dịch của một mã, hãy nhập lệnh:\n`xoa [Mã]`\n\n*Ví dụ:* `xoa BTC`",
                "buttons": ["🪙 Crypto", "🏠 Trang chủ"]
            }

        if isinstance(data, str) and data.lower().startswith("xoa "):
            try:
                ticker_to_del = data.split(" ")[1].upper()
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    # Xóa giao dịch CRYPTO trong bảng chung
                    cursor.execute("DELETE FROM transactions WHERE user_id = ? AND ticker = ? AND asset_type = 'CRYPTO'", (user_id, ticker_to_del))
                    conn.commit()
                return f"✅ Đã xóa toàn bộ giao dịch mã *{ticker_to_del}*."
            except Exception as e:
                return f"⚠️ Lỗi khi xóa: {str(e)}"

        # Báo cáo
        if data == "📈 Báo cáo":
            pf_data = pm.get_crypto_portfolio()
            s = pf_data['summary']
            if not pf_data['positions']: return "⚠️ Bạn chưa có dữ liệu để lập báo cáo."
            
            report = (
                f"📈 *BÁO CÁO HIỆU SUẤT CRYPTO*\n\n"
                f"💰 Tổng vốn ròng: `{self.format_money(s['total_cost'])}`\n"
                f"💵 Giá trị hiện tại: `{self.format_money(s['total_value'])}`\n"
                f"📊 Tổng lãi/lỗ: *{self.format_money(s['total_profit'])}*\n"
                f"🚀 Tỷ suất (ROI): `{s['total_roi']:+.2f}%`\n\n"
                f"⬆️ Tổng nạp: {self.format_money(pf_data['total_in'])}\n"
                f"⬇️ Tổng rút: {self.format_money(pf_data['total_out'])}\n\n"
                f"🔥 *Đánh giá:* " + ("Danh mục Crypto đang tăng trưởng tốt!" if s['total_roi'] > 0 else "Nên rà soát lại các vị thế.")
            )
            return {"status": "wizard", "message": report, "buttons": ["➕ Giao dịch", "🪙 Crypto", "🏠 Trang chủ"]}

        # --- 2. HIỂN THỊ DANH MỤC (LAYOUT ĐỒNG BỘ STOCK) ---
        pf_data = pm.get_crypto_portfolio()
        s = pf_data['summary']
        positions = pf_data['positions']
        
        if not positions:
            msg = "🪙 *DANH MỤC CRYPTO*\n\nBạn chưa có coin nào trong danh mục."
        else:
            res = (
                f"🪙 *DANH MỤC CRYPTO*\n\n"
                f"💰 Tổng giá trị:\n*{self.format_money(s['total_value'])}*\n"
                f"💵 Tổng vốn: {self.format_money(s['total_cost'])}\n"
                f"📈 Lãi: {self.format_money(s['total_profit'])} ({s['total_roi']:+.1f}%)\n\n"
                f"⬆️ Tổng nạp: {self.format_money(pf_data['total_in'])}\n"
                f"⬇️ Tổng rút: {self.format_money(pf_data['total_out'])}\n\n"
            )

            if s.get('best'):
                res += f"🏆 Tốt nhất: {s['best']['ticker']} ({s['best']['roi']:+.1f}%)\n"
                res += f"📉 Kém nhất: {s['worst']['ticker']} ({s['worst']['roi']:+.1f}%)\n"
                weight = (s['largest']['market_value'] / s['total_value'] * 100) if s['total_value'] > 0 else 0
                res += f"📊 Tỉ trọng lớn: {s['largest']['ticker']} ({weight:.1f}%)\n"
                res += "────────────\n"

            for p in positions:
                # Định dạng số lượng gọn gàng
                qty_display = f"{p['qty']:.4f}".rstrip('0').rstrip('.')
                res += (
                    f"\n*{p['ticker']}*\n"
                    f"SL: `{qty_display}`\n"
                    f"Vốn TB: `${p['avg_price']:,.1f}`\n"
                    f"Giá HT: `${p['current_price']:,.1f}`\n"
                    f"Giá trị: {self.format_money(p['market_value'])}\n"
                    f"Lãi: {self.format_money(p['profit'])} ({p['roi']:+.1f}%)\n"
                    f"────────────"
                )
            msg = res

        return {
            "status": "wizard",
            "message": msg,
            "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo", "❌ Xóa mã", "🏠 Trang chủ"]
        }
