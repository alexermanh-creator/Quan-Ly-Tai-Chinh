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

async def format_response(update: Update, m_id: str, result: dict):
    main_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
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
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 Tiền mặt: {result.get('cash_val', '0đ')}\n"
            f"🏠 Bấm các nút dưới để quản lý chi tiết."
        )
        await update.message.reply_text(msg, reply_markup=main_markup, parse_mode="Markdown")
        return

    if isinstance(result, dict) and result.get("status") == "wizard":
        keyboard = [result["buttons"][i:i+2] for i in range(0, len(result["buttons"]), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")
        return

    await update.message.reply_text(str(result), reply_markup=main_markup, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("💼 *QUẢN LÝ TÀI SẢN*", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    if text in ["🏠 Trang chủ", "💼 Tài sản của bạn"]:
        await format_response(update, 'dashboard', modules['dashboard'].run(user_id))
        return
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            await format_response(update, m_id, m_instance.run(user_id))
            return
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        if isinstance(res, dict) and res.get("status") == "wizard":
            await format_response(update, 'transaction', res)
        else:
            await update.message.reply_text(str(res))
