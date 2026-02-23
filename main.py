import os
from app.telegram.bot_client import TelegramClient

if __name__ == "__main__":
    print("--- Đang khởi động Platform Multi-Client ---")
    
    # Kiểm tra biến môi trường
    if not os.getenv("TELEGRAM_TOKEN"):
        print("❌ LỖI: Chưa cấu hình TELEGRAM_TOKEN trên Railway!")
    else:
        # Khởi chạy Telegram Client
        client = TelegramClient()
        client.run()