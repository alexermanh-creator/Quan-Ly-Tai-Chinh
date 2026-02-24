import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# 1. Nạp tất cả module tự động
modules = load_all_modules()

# 2. Định nghĩa Menu chính
MAIN_MENU = [
    ["💼 Tài sản của bạn"],
    ["📊 Cổ phiếu", "🪙 Crypto"],
    ["🥇 Đầu tư khác", "➕ Giao dịch"],
    ["📜 Lịch sử", "🎯 Mục tiêu"],
    ["📈 Báo cáo", "⚙️ Cài đặt"],
    ["🤖 Trợ lý AI", "🏠 Trang chủ"]
]

# 3. Hàm định dạng phản hồi "Vạn năng" (Sửa lỗi NameError và Hiển thị)
async def format_response(update: Update, m_id: str, result: dict):
    """Hàm này sẽ xử lý hiển thị cho TẤT CẢ các module (Dashboard, Crypto, Stock...)"""
    main_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    
    # TRƯỜNG HỢP 1: Giao diện Dashboard tổng
    if m_id == "dashboard" and isinstance(result, dict):
        msg = (
            f"💼 *TÀI SẢN CỦA BẠN*\n"
            f"💰 Tổng: `{result.get('display_total', '0đ')}`\n"
            f"📈 Lãi: `{result.get('display_profit', '0đ')}` ({result.get('profit_percent', '0%')})\n\n"
            f"📊 Stock: {result.get('stock_val', '0đ')}\n"
            f"🪙 Crypto: {result.get('crypto_val', '0đ')}\n"
            f"🥇 Khác: {result.get('other_val', '0đ')}\n\n"
            f"🎯 Mục tiêu: `{result.get('goal_display', '500 triệu')}`\n"
            f"Tiến độ: `{result.get('goal_progress', 0):,.1f}%`\n"
            f"Còn thiếu: `{result.get('remain_display', '0đ')}`\n\n"
            f"⬆️ Tổng nạp: {result.get('total_in', '0đ')}\n"
            f"⬇️ Tổng rút: {result.get('total_out', '0đ')}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 Tiền mặt: {result.get('cash_val', '0đ')}\n"
            f"📊 Cổ phiếu: {result.get('stock_val', '0đ')}\n"
            f"🪙 Crypto: {result.get('crypto_val', '0đ')}\n\n"
            f"🏠 Bấm các nút dưới để quản lý chi tiết."
        )
        await update.message.reply_text(msg, reply_markup=main_markup, parse_mode="Markdown")
        return

    # TRƯỜNG HỢP 2: Các module dạng Wizard (Crypto, Stock, Transaction...)
    if isinstance(result, dict) and result.get("status") == "wizard":
        msg_text = result.get("message", "Đang xử lý...")
        buttons = result.get("buttons", ["🏠 Trang chủ"])
        # Tự động chia nút bấm thành 2 cột
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(msg_text, reply_markup=markup, parse_mode="Markdown")
        return

    # TRƯỜNG HỢP 3: Phản hồi dạng chuỗi văn bản đơn giản
    final_text = result if isinstance(result, str) else "⚠️ Lỗi xử lý dữ liệu module."
    await update.message.reply_text(final_text, reply_markup=main_markup, parse_mode="Markdown")

# 4. Các hàm xử lý sự kiện Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("💼 *QUẢN LÝ TÀI SẢN VÀ ĐẦU TƯ*", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # Ưu tiên nút điều hướng chính
    if text in ["🏠 Trang chủ", "❌ Hủy", "💼 Tài sản của bạn"]:
        if 'dashboard' in modules:
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

    # Quét các module (Crypto, Stock...) để xử lý
    for m_id, m_instance in modules.items():
        info = m_instance.get_info()
        # Nếu bấm đúng tên nút (ví dụ "🪙 Crypto") hoặc module tự nhận lệnh
        if (info['name'] == text) or (hasattr(m_instance, 'can_handle') and m_instance.can_handle(text)):
            result = m_instance.run(user_id, text if hasattr(m_instance, 'can_handle') and m_instance.can_handle(text) else None)
            await format_response(update, m_id, result)
            return

    # Xử lý nhập liệu giao dịch nhanh (btc 1 95000...)
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        if res == "EXIT_SIGNAL":
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return
        
        if isinstance(res, str):
            if any(x in res for x in ["thành công", "hủy"]):
                result = modules['dashboard'].run(user_id)
                await update.message.reply_text(res)
                await format_response(update, 'dashboard', result)
            else:
                await update.message.reply_text(res)
            return
        elif isinstance(res, dict) and res.get("status") == "wizard":
            await format_response(update, 'transaction', res)
            return

    await update.message.reply_text("❓ Tôi chưa hiểu lệnh này. Hãy chọn Menu hoặc nhập lệnh nhanh.")
