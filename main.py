import os
import sys
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.telegram.bot_client import start, handle_message

# Bản vá tương thích Python 3.13 cho Railway
if sys.version_info >= (3, 13):
    import telegram.ext._updater
    telegram.ext._updater.Updater.__init__ = lambda self, *args, **kwargs: setattr(self, '_Updater__polling_cleanup_cb', None)

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        sys.exit("❌ LỖI: Thiếu TELEGRAM_TOKEN")

    print("🚀 Bot đang khởi động với Layout Mục 5 & 10...")
    
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling(drop_pending_updates=True, stop_signals=None)
