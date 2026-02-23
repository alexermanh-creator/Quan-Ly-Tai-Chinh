import os
import sys
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Patch cho Python 3.13 (Giữ nguyên để tránh lỗi cũ)
if sys.version_info >= (3, 13):
    import telegram.ext._updater
    telegram.ext._updater.Updater.__init__ = lambda self, *a, **k: setattr(self, '_Updater__polling_cleanup_cb', None)

from app.telegram.bot_client import start, handle_message

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    print("🚀 Đang khởi động hệ thống...")
    
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling(drop_pending_updates=True)
