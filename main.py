import os
from app.telegram.bot_client import setup_app

if __name__ == "__main__":
    print("--- KHỞI ĐỘNG HỆ THỐNG TÀI CHÍNH ---")
    
    app = setup_app()
    if app:
        # Thêm các handler trực tiếp tại đây để đảm bảo an toàn luồng
        from app.telegram.bot_client import start, handle_message
        from telegram.ext import CommandHandler, MessageHandler, filters
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("🚀 Hệ thống đã sẵn sàng nhận lệnh.")
        app.run_polling(drop_pending_updates=True)
