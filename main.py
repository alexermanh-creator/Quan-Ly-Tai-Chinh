import os
import sys
import logging

# 1. Cấu hình Logging để theo dõi quá trình tự thích ứng
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_strategy_a(token):
    """Chiến thuật A: Sử dụng ApplicationBuilder với bản vá lỗi cho Python 3.13"""
    print("--- 🛡️ Đang thử khởi động Bản A (High-Level) ---")
    
    # Bản vá khẩn cấp cho Python 3.13
    if sys.version_info >= (3, 13):
        try:
            import telegram.ext._updater
            def mock_init(self, *args, **kwargs):
                self._Updater__polling_cleanup_cb = None
            telegram.ext._updater.Updater.__init__ = mock_init
            print("✅ Đã áp dụng bản vá tương thích Python 3.13")
        except Exception as e:
            print(f"⚠️ Không thể áp dụng bản vá: {e}")

    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
    from app.telegram.bot_client import start, handle_message
    
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Bản A đã sẵn sàng. Đang kết nối Telegram...")
    app.run_polling(drop_pending_updates=True)

def run_strategy_b(token):
    """Chiến thuật B: Sử dụng cách khởi tạo trực tiếp (Bypass Builder)"""
    print("--- 🛠️ Bản A thất bại. Chuyển sang Bản B (Direct Access) ---")
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    from app.telegram.bot_client import start, handle_message
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bản B đã sẵn sàng. Đang kết nối Telegram...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ LỖI: Thiếu TELEGRAM_TOKEN trong cấu hình Railway.")
        sys.exit(1)

    # Vòng lặp tự thích ứng
    try:
        run_strategy_a(token)
    except Exception as error_a:
        print(f"❌ Bản A lỗi: {error_a}")
        try:
            run_strategy_b(token)
        except Exception as error_b:
            print(f"❌ Bản B cũng lỗi: {error_b}")
            print("❗ Hệ thống không thể khởi động. Vui lòng kiểm tra lại thư viện.")
