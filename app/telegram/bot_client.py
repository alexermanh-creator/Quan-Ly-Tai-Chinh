import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from backend.module_loader import load_all_modules

# Thiết lập nhật ký lỗi
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class TelegramClient:
    def __init__(self):
        self.modules = load_all_modules()
        self.token = os.getenv("TELEGRAM_TOKEN")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = []
        for m_id, m_instance in self.modules.items():
            keyboard.append([m_instance.get_info()['name']])
            
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "💎 Hệ thống Quản lý Tài chính Pro đã sẵn sàng.\n"
            "Vui lòng chọn tính năng bên dưới:",
            reply_markup=reply_markup
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        for m_id, m_instance in self.modules.items():
            if m_instance.get_info()['name'] == text:
                # Thực thi module từ backend
                result = m_instance.run(update.effective_user.id)
                
                if m_id == "dashboard":
                    msg = (
                        f"📊 **BẢNG ĐIỀU KHIỂN TÀI SẢN**\n\n"
                        f"💰 Tổng tài sản: {result['total_assets']:,.0f} VNĐ\n"
                        f"📈 Lãi/Lỗ: {result['profit_loss']:,.0f} VNĐ ({result['profit_percent']}%)\n"
                        f"🎯 Tiến độ: {result['goal_progress']}%\n\n"
                        f"_{result['message']}_"
                    )
                    await update.message.reply_text(msg, parse_mode="Markdown")
                else:
                    await update.message.reply_text(f"✅ Kết quả: {result}")
                return

    def build_application(self):
        """Khởi tạo và cấu hình Application thay vì chạy trực tiếp"""
        if not self.token:
            print("❌ LỖI: Thiếu TELEGRAM_TOKEN")
            return None
            
        application = Application.builder().token(self.token).build()
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        return application
