import os
from app.telegram.bot_client import TelegramClient

if __name__ == "__main__":
    print("--- Đang khởi động Platform Multi-Client ---")
    
    try:
        client = TelegramClient()
        app = client.build_application()
        
        if app:
            print("🚀 Bot đang bắt đầu nhận tin nhắn (Polling)...")
            app.run_polling(drop_pending_updates=True)
        else:
            print("❌ Không thể khởi tạo Application.")
            
    except Exception as e:
        print(f"❌ LỖI KHỞI CHẠY: {e}")
