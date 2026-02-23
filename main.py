import os
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from backend.module_loader import load_all_modules

# Khóa cứng Logging
logging.basicConfig(level=logging.INFO)

# Nạp Module
modules = load_all_modules()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[m.get_info()['name']] for m in modules.values()]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("💎 Hệ thống Tài chính Online", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            res = m_instance.run(update.effective_user.id)
            await update.message.reply_text(f"【{text}】\n{str(res)}")
            return

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ ERROR: Missing Token")
    else:
        # Sử dụng ApplicationBuilder với cấu hình tối giản tuyệt đối
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("🚀 BOT IS LIVE")
        app.run_polling(drop_pending_updates=True)
