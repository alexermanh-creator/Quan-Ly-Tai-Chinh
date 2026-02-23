import os
from app.telegram.bot_client import setup_app

if __name__ == "__main__":
    print("--- Khởi động Platform Hệ thống ---")
    
    app = setup_app()
    if app:
        print("🚀 Bot đang bắt đầu nhận tin nhắn...")
        # Lệnh chạy quan trọng nhất cho Railway
        app.run_polling(drop_pending_updates=True)
    else:
        print("❌ LỖI: Thiếu TELEGRAM_TOKEN trong Variables của Railway.")
