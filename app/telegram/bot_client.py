import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# Khởi tạo logging để bạn xem lỗi trên Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Nạp module
modules = load_all_modules()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Layout Menu chính theo Mục 5 của bạn"""
    keyboard = [
        ["💼 Tài sản của bạn"],
        ["📊 Cổ phiếu", "🪙 Crypto"],
        ["🥇 Khác", "➕ Giao dịch"],
        ["📜 Lịch sử", "🎯 Mục tiêu"],
        ["📈 Báo cáo", "⚙️ Cài đặt"],
        ["🤖 Trợ lý AI", "🏠 Home"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "💼 *QUẢN LÝ TÀI SẢN VÀ ĐẦU TƯ*\nHệ thống đã sẵn sàng.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bộ điều phối tin nhắn - Đã thêm DEBUG để kiểm tra lỗi Matching"""
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    print(f"DEBUG: Nhận tin nhắn từ User: [{text}]")

    # 1. Khớp lệnh dựa trên nút bấm (Matching logic)
    for m_id, m_instance in modules.items():
        m_info = m_instance.get_info()
        print(f"DEBUG: Đang so sánh [{text}] với [{m_info['name']}]")
        
        if text == m_info['name']:
            result = m_instance.run(user_id)
            await format_response(update, m_id, result)
            return

    # 2. Khớp lệnh nhập liệu (Nếu có số tiền)
    if any(char.isdigit() for char in text):
        if 'transaction' in modules:
            res = modules['transaction'].run(user_id, text)
            await update.message.reply_text(res)
            return

    await update.message.reply_text("❓ Tôi không hiểu lệnh này. Vui lòng bấm Menu.")

async def format_response(update: Update, m_id: str, result: dict):
    """Layout Chi tiết theo Mục 10 của bạn"""
    if m_id == "dashboard":
        # Công thức tính "Còn thiếu" dựa trên mục tiêu 500 triệu
        goal = 500
        total = result.get('total_assets', 0)
        missing = goal - total
        
        msg = (
            f"💼 *TÀI SẢN CỦA BẠN*\n"
            f"💰 Tổng: `{total:,.0f} triệu`\n"
            f"📈 Lãi: `{result.get('profit_loss', 0):,.0f} triệu` ({result.get('profit_percent', 0)}%)\n\n"
            f"📊 Stock: +12 triệu (+11%)\n"
            f"🪙 Crypto: -40 triệu (-63%)\n"
            f"🥇 Khác: -3 triệu (-6%)\n\n"
            f"🎯 Mục tiêu: `{goal} triệu`\n"
            f"Tiến độ: `{result.get('goal_progress', 0)}%`\n"
            f"Còn thiếu: `{missing:,.0f} triệu`\n\n"
            f"⬆️ Tổng nạp: 210 triệu\n"
            f"⬇️ Tổng rút: 20 triệu\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 Tiền mặt: 10 triệu (7%)\n"
            f"📊 Cổ phiếu: 120 triệu (84%)\n"
            f"🪙 Crypto: 23 triệu (16%)\n"
            f"🥇 Khác: -10 triệu (-7%)"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"✅ Kết quả từ {m_id}: {result}")
