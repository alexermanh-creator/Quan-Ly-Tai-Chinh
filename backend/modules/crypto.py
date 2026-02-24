from backend.interface import BaseModule
from backend.core.portfolio_crypto import CryptoPortfolio
from backend.database.db_manager import db

class Module(BaseModule):
    def get_info(self):
        return {"id": "crypto", "name": "🪙 Crypto"}

    def can_handle(self, text):
        btns = ["🪙 Crypto", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa coin"]
        return text in btns or text.lower().startswith(("price ", "del "))

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
        cp = CryptoPortfolio(user_id)

        # --- XỬ LÝ LỆNH ---
        if data == "🔄 Cập nhật giá":
            return {"status": "wizard", "message": "🔄 *CẬP NHẬT GIÁ CRYPTO*\nNhập: `price [Mã] [Giá_USD]`\nVD: `price BTC 65000`", "buttons": ["🪙 Crypto", "🏠 Trang chủ"]}
        
        if isinstance(data, str) and data.lower().startswith("price "):
            try:
                _, t, p = data.split()
                with db.get_connection() as conn:
                    conn.execute("INSERT OR REPLACE INTO crypto_prices (symbol, price_usd) VALUES (?, ?)", (t.upper(), float(p)))
                return f"✅ Đã cập nhật giá {t.upper()}"
            except: return "⚠️ Sai cú pháp."

        # --- HIỂN THỊ LAYOUT DEMO FINAL ---
        d = cp.get_data()
        s = d['summary']
        
        res = (
            f"🏆\n*DEMO FINAL — CRYPTO*\n"
            f"🪙\n*DANH MỤC CRYPTO*\n\n"
            f"💰 Tổng giá trị:\n{self.format_money(s['total_value'])}\n"
            f"💵 Tổng vốn: {self.format_money(s['total_cost'])}\n"
            f"📉 Lỗ: {self.format_money(s['total_profit'])} ({s['total_roi']:+.1f}%)\n\n"
            f"⬆️ Tổng nạp: {self.format_money(d['total_in'])}\n"
            f"⬇️ Tổng rút: {self.format_money(d['total_out'])}\n\n"
        )
        
        if s['best']:
            res += f"🏆 Coin tốt nhất: {s['best']['symbol']} ({s['best']['roi']:+.1f}%)\n"
            res += f"📉 Coin kém nhất: {s['worst']['symbol']} ({s['worst']['roi']:+.1f}%)\n"
            weight = (s['largest']['market_value'] / s['total_value'] * 100) if s['total_value'] > 0 else 0
            res += f"📊 Tỉ trọng lớn nhất: {s['largest']['symbol']} ({weight:.0f}%)\n"

        for p in d['positions']:
            res += (
                f"\n\n────────────\n\n"
                f"*{p['symbol']}*\n\n"
                f"SL: `{p['qty']}`\n\n"
                f"Giá vốn TB: `{p['avg_price']:,.0f}`\n\n"
                f"Giá hiện tại: `{p['current_price']:,.0f}`\n\n"
                f"Giá trị: {self.format_money(p['market_value'])}\n\n"
                f"Lãi: {self.format_money(p['profit'])} ({p['roi']:+.1f}%)\n"
            )

        return {
            "status": "wizard",
            "message": res + "\n\n📱\n*MENU CRYPTO MODULE*",
            "buttons": ["➕ Giao dịch", "🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa coin", "🏠 Trang chủ"]
        }
