import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from backend.module_loader import load_all_modules

# Khởi tạo logger để theo dõi lỗi chính xác
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Nạp sẵn module để dùng chung
modules = load_all_modules()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[m.get_info()['name']] for m in modules.values()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "💎 Hệ thống Quản lý Tài chính Pro đã sẵn sàng.\nChọn tính năng:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(update.effective_user.id)
            # Format đơn giản để đảm bảo không lỗi hiển thị
            await update.message.reply_text(f"Kết quả từ {text}: {str(result)}")
            return

def setup_app():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        return None
    
    # Sử dụng ApplicationBuilder chuẩn của thư viện v20.x
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
