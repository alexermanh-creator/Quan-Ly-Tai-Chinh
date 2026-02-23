import os
import sys
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.telegram.bot_client import start, handle_message

# Fix lỗi tương thích Python 3.13 cho Railway
if sys.version_info >= (3, 13):
    import telegram.ext._updater
    telegram.ext._updater.Updater.__init__ = lambda self, *a, **k: setattr(self, '_Updater__polling_cleanup_cb', None)

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ THIẾU TELEGRAM_TOKEN")
        sys.exit(1)

    print("🚀 Đang khởi động hệ thống...")
    
    app = ApplicationBuilder().token(token).build()
    
    # Kết nối các hàm xử lý từ bot_client.py
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Chạy dọn dẹp kết nối cũ và bắt đầu nhận tin nhắn
    app.run_polling(drop_pending_updates=True, stop_signals=None)
