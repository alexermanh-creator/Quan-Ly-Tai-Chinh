from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
from backend.module_loader import load_all_modules

load_dotenv()

class TelegramClient:
    def __init__(self):
        self.modules = load_all_modules()
        self.token = os.getenv("TELEGRAM_TOKEN")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hàm chào mừng và hiển thị danh sách module dưới dạng menu"""
        keyboard = []
        # Tự động tạo nút bấm từ danh sách module đang có
        for m_id, m_instance in self.modules.items():
            keyboard.append([m_instance.get_info()['name']])
            
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "💎 Hệ thống Quản lý Tài chính Pro đã sẵn sàng.\n"
            "Vui lòng chọn tính năng bên dưới:",
            reply_markup=reply_markup
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý khi người dùng bấm vào menu"""
        text = update.message.text
        # Tìm xem module nào có tên khớp với nút vừa bấm
        for m_id, m_instance in self.modules.items():
            if m_instance.get_info()['name'] == text:
                result = m_instance.run(update.effective_user.id)
                
                # Logic hiển thị chuyên nghiệp cho Dashboard
                if m_id == "dashboard":
                    msg = (
                        f"📊 **BẢNG ĐIỀU KHIỂN TÀI SẢN**\n\n"
                        f"💰 Tổng tài sản: {result['total_assets']:,.0f} VNĐ\n"
                        f"📈 Lãi/Lỗ: {result['profit_loss']:,.0f} VNĐ ({result['profit_percent']}%)\n"
                        f"🎯 Tiến độ mục tiêu: {result['goal_progress']}%\n\n"
                        f"_{result['message']}_"
                    )
                    await update.message.reply_text(msg, parse_mode="Markdown")
                else:
                    await update.message.reply_text(str(result))
                return

    def run(self):
        application = Application.builder().token(self.token).build()
        application.add_handler(CommandHandler("start", self.start))
        # (Sẽ thêm Handler xử lý tin nhắn văn bản ở bước sau để demo mượt hơn)
        application.run_polling()