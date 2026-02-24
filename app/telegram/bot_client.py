import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

modules = load_all_modules()

MAIN_MENU = [
    ["💼 Tài sản của bạn"],
    ["📊 Cổ phiếu", "🪙 Crypto"],
    ["🥇 Đầu tư khác", "➕ Giao dịch"],
    ["📜 Lịch sử", "🎯 Mục tiêu"],
    ["📈 Báo cáo", "⚙️ Cài đặt"],
    ["🤖 Trợ lý AI", "🏠 Trang chủ"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("💼 *QUẢN LÝ TÀI SẢN VÀ ĐẦU TƯ*", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # --- 1. ĐIỀU HƯỚNG CHÍNH ---
    if text in ["🏠 Trang chủ", "❌ Hủy", "🏠 Home", "💼 Tài sản của bạn"]:
        if 'dashboard' in modules:
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

    # --- 2. CƠ CHẾ PLUG & PLAY (QUAN TRỌNG NHẤT) ---
    # Bot không cần biết 'text' là gì, nó chỉ hỏi các module xem ai nhận lệnh này
    for m_id, m_instance in modules.items():
        # Nếu module tự nhận lệnh (qua can_handle) hoặc khớp tên Menu
        if m_instance.can_handle(text) or m_instance.get_info()['name'] == text:
            result = m_instance.run(user_id, text if m_instance.can_handle(text) else None)
            
            # Xử lý nếu module trả về text thông báo thành công (như sau khi gia/xoa)
            if isinstance(result, str):
                await update.message.reply_text(result, parse_mode="Markdown")
                # Sau khi xong việc, tự động reload lại chính module đó để hiện layout chi tiết
                refresh = m_instance.run(user_id)
                await format_response(update, m_id, refresh)
            else:
                await format_response(update, m_id, result)
            return

    # --- 3. XỬ LÝ GIAO DỊCH (TRANSACTION PARSER) ---
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        if res == "EXIT_SIGNAL":
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
        elif isinstance(res, str):
            await update.message.reply_text(res)
            if any(x in res for x in ["thành công", "Trang chủ"]):
                await format_response(update, 'dashboard', modules['dashboard'].run(user_id))
        elif isinstance(res, dict) and res.get("status") == "wizard":
            await format_response(update, 'transaction', res)
        return

    await update.message.reply_text("❓ Tôi chưa hiểu lệnh này. Hãy chọn Menu.")

async def format_response(update: Update, m_id: str, result: dict):
    """Giao diện hiển thị: Tuyệt đối giữ nguyên Layout của từng Module"""
    main_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    
    if m_id == "dashboard":
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
            f"🪙 Crypto: {result.get('crypto_val', '0đ')}\n"
            f"🥇 Khác: {result.get('other_val', '0đ')}\n\n"
            f"🏠 Bấm các nút dưới để quản lý chi tiết."
        )
        await update.message.reply_text(msg, reply_markup=main_markup, parse_mode="Markdown")
    elif isinstance(result, dict) and result.get("status") == "wizard":
        buttons = result["buttons"]
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(str(result), reply_markup=main_markup, parse_mode="Markdown")
