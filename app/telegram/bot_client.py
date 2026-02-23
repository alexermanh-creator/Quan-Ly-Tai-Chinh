import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# Nạp module một lần duy nhất
modules = load_all_modules()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Giao diện Menu chính"""
    keyboard = [[m.get_info()['name']] for m in modules.values()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "💎 *HỆ THỐNG TÀI CHÍNH PERSONAL PRO*\n"
        "Chào mừng bạn quay trở lại. Vui lòng chọn tính năng:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bộ điều phối thông minh: Tự nhận diện nút bấm hoặc dữ liệu nhập vào"""
    text = update.message.text
    user_id = update.effective_user.id

    # Bước 1: Kiểm tra xem có phải bấm nút Menu không
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(user_id)
            await format_response(update, m_id, result)
            return

    # Bước 2: Nếu không phải nút bấm, kiểm tra xem có phải đang nhập số tiền không
    # Ví dụ: "CASH 500000" hoặc "SAVING 1000000"
    if any(char.isdigit() for char in text):
        if 'transaction' in modules:
            res = modules['transaction'].run(user_id, text)
            await update.message.reply_text(res)
        else:
            await update.message.reply_text("❌ Module Giao dịch chưa được cài đặt.")
    else:
        await update.message.reply_text("❓ Tôi không hiểu lệnh này. Vui lòng chọn Menu hoặc nhập đúng cú pháp tài sản.")

async def format_response(update: Update, m_id: str, result: dict):
    """Hàm làm đẹp dữ liệu trước khi gửi cho khách hàng"""
    if m_id == "dashboard":
        msg = (
            f"📊 *BẢNG ĐIỀU KHIỂN TÀI SẢN*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 Tổng tài sản: `{result['total_assets']:,.0f} VNĐ`\n"
            f"📈 Lãi/Lỗ: `{result['profit_loss']:,.0f} VNĐ` ({result['profit_percent']}%)\n"
            f"🎯 Tiến độ: {result['goal_progress']}%\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"ℹ️ _{result['message']}_"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    elif m_id == "system_health":
        msg = f"✅ *HỆ THỐNG:* {result['status']}\n🕒 *GIỜ:* {result['timestamp']}\n💬 {result['message']}"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(str(result))
