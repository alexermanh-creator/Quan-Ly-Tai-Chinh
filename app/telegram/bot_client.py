import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from backend.module_loader import load_all_modules

# Tắt các logging không cần thiết để logs sạch hơn
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Nạp module
modules = load_all_modules()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hàm khởi tạo Menu"""
    keyboard = [[m.get_info()['name']] for m in modules.values()]
    if not keyboard:
        keyboard = [["Chưa có module"]]
        
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "💎 Hệ thống Quản lý Tài chính Pro\nTrạng thái: Online",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý điều hướng module"""
    text = update.message.text
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(update.effective_user.id)
            await update.message.reply_text(f"【{text}】\n{str(result)}")
            return

def setup_app():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ LỖI: Thiếu biến TELEGRAM_TOKEN")
        return None
    
    # Khởi tạo qua ApplicationBuilder
    return ApplicationBuilder().token(token).build()
