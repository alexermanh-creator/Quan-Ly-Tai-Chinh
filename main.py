import os
from app.telegram.bot_client import TelegramClient

if __name__ == "__main__":
    print("--- Đang khởi động Platform Multi-Client ---")
    
    try:
        client = TelegramClient()
        client.run()
    except Exception as e:
        print(f"❌ LỖI KHỞI CHẠY: {e}")