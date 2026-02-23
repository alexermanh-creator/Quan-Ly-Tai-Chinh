import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# Nạp module một lần duy nhất
modules = load_all_modules()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Thay thế đoạn keyboard cũ bằng cấu trúc phân tầng này:
    keyboard = [
        ["💼 Tài sản của bạn"],             # Hàng 1: Nút to nhất
        ["📊 Cổ phiếu", "🪙 Crypto"],        # Hàng 2: 2 nút
        ["🥇 Khác", "➕ Giao dịch"],         # Hàng 3: 2 nút
        ["📜 Lịch sử", "🎯 Mục tiêu"],       # Hàng 4: 2 nút
        ["📈 Báo cáo", "⚙️ Cài đặt"],        # Hàng 5: 2 nút
        ["🤖 Trợ lý AI", "🏠 Home"]           # Hàng 6: 2 nút
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # Sửa lại nội dung tin nhắn chào mừng cho Pro
    await update.message.reply_text(
        "💼 *QUẢN LÝ TÀI SẢN VÀ ĐẦU TƯ*\n"
        "Hệ thống đã sẵn sàng phục vụ.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bộ điều phối thông minh: Tự nhận diện nút bấm hoặc dữ liệu nhập vào"""
    text = update.message.text
    user_id = update.effective_user.id

    # Bước 1: Kiểm tra xem có phải bấm nút Menu không
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(user_id)
            await format_response(update, m_id, result)
            return

    # Bước 2: Nếu không phải nút bấm, kiểm tra xem có phải đang nhập số tiền không
    # Ví dụ: "CASH 500000" hoặc "SAVING 1000000"
    if any(char.isdigit() for char in text):
        if 'transaction' in modules:
            res = modules['transaction'].run(user_id, text)
            await update.message.reply_text(res)
        else:
            await update.message.reply_text("❌ Module Giao dịch chưa được cài đặt.")
    else:
        await update.message.reply_text("❓ Tôi không hiểu lệnh này. Vui lòng chọn Menu hoặc nhập đúng cú pháp tài sản.")

async def format_response(update: Update, m_id: str, result: dict):
    """Hàm làm đẹp dữ liệu trước khi gửi cho khách hàng"""
    if m_id == "dashboard":
        # Các biến này sẽ lấy từ result (Module Dashboard trả về)
        msg = (
            f"💼 *TÀI SẢN CỦA BẠN*\n"
            f"💰 Tổng: `{result['total_assets']:,.0f} triệu`\n"
            f"📈 Lãi: `{result['profit_loss']:,.0f} triệu` ({result['profit_percent']}%)\n\n"
            
            f"📊 Stock: +12 triệu (+11%)\n"
            f"🪙 Crypto: -40 triệu (-63%)\n"
            f"🥇 Khác: -3 triệu (-6%)\n\n"
            
            f"🎯 Mục tiêu: `500 triệu`\n"
            f"Tiến độ: `{result['goal_progress']}%`\n"
            f"Còn thiếu: `{500 - result['total_assets']:,.0f} triệu`\n\n"
            
            f"⬆️ Tổng nạp: 210 triệu\n"
            f"⬇️ Tổng rút: 20 triệu\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 Tiền mặt: 10 triệu (7%)\n"
            f"📊 Cổ phiếu: 120 triệu (84%)\n"
            f"🪙 Crypto: 23 triệu (16%)\n"
            f"🥇 Khác: -10 triệu (-7%)"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        await update.message.reply_text(msg, parse_mode="Markdown")
    elif m_id == "system_health":
        msg = f"✅ *HỆ THỐNG:* {result['status']}\n🕒 *GIỜ:* {result['timestamp']}\n💬 {result['message']}"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(str(result))

