import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from backend.module_loader import load_all_modules

# 1. Cấu hình Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. Nạp Module
modules = load_all_modules()

# 3. Định nghĩa các hàm xử lý trực tiếp
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[m.get_info()['name']] for m in modules.values()]
    if not keyboard: keyboard = [["Chưa có module"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("💎 Hệ thống Tài chính Online", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(update.effective_user.id)
            await update.message.reply_text(f"【{text}】\n{str(result)}")
            return

# 4. Chạy ứng dụng
if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ Thiếu TELEGRAM_TOKEN")
    else:
        print("🚀 Đang khởi động Bot...")
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run_polling(drop_pending_updates=True)
