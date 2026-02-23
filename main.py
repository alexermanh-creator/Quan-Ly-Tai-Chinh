import os
import sys
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.telegram.bot_client import start, handle_message

# Vá lỗi cho Python 3.13 trên Railway
if sys.version_info >= (3, 13):
    import telegram.ext._updater
    telegram.ext._updater.Updater.__init__ = lambda self, *a, **k: setattr(self, '_Updater__polling_cleanup_cb', None)

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    
    if not token:
        print("❌ LỖI: Thiếu TELEGRAM_TOKEN")
        sys.exit(1)

    print("🚀 Hệ thống đang dọn dẹp kết nối cũ và khởi động...")
    
    # Khởi tạo Application
    app = ApplicationBuilder().token(token).build()
    
    # Đăng ký các lệnh
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Chạy Bot - Chú ý: Thụt lề đúng 4 dấu cách (1 tab)
    app.run_polling(drop_pending_updates=True, stop_signals=None)
