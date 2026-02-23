import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# Nạp tất cả module
modules = load_all_modules()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """LAYOUT DASHBOARD - Mục 5"""
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
        "💼 *QUẢN LÝ TÀI SẢN VÀ ĐẦU TƯ*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ĐIỀU PHỐI TIN NHẮN: Nút bấm -> Parser nhanh -> Báo lỗi"""
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # 1. ƯU TIÊN KIỂM TRA NÚT BẤM
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(user_id)
            await format_response(update, m_id, result)
            return

    # 2. KIỂM TRA LỆNH NHẬP TẮT (Parser nhanh)
    if any(char.isdigit() for char in text) or " " in text:
        if 'transaction' in modules:
            res = modules['transaction'].run(user_id, text)
            if isinstance(res, str):
                await update.message.reply_text(res)
                return

    # 3. NẾU CẢ 2 ĐỀU KHÔNG KHỚP
    await update.message.reply_text("❓ Tôi chưa hiểu lệnh này. Vui lòng chọn Menu hoặc nhập đúng cú pháp (VD: hpg 500 28.5)")

async def format_response(update: Update, m_id: str, result: dict):
    """LAYOUT CHI TIẾT - Mục 10"""
    if m_id == "dashboard":
        total = result.get('total_assets', 0)
        goal = result.get('goal_value', 500)
        
        msg = (
            f"💼 *TÀI SẢN CỦA BẠN*\n"
            f"💰 Tổng: `{total:,.0f} triệu`\n"
            f"📈 Lãi: `{result.get('profit_loss', 0)} triệu` ({result.get('profit_percent', 0)}%)\n\n"
            f"📊 Stock: +12 triệu (+11%)\n"
            f"🪙 Crypto: -40 triệu (-63%)\n"
            f"🥇 Khác: -3 triệu (-6%)\n\n"
            f"🎯 Mục tiêu: `{goal} triệu`\n"
            f"Tiến độ: `{result.get('goal_progress', 0)}%`\n"
            f"Còn thiếu: `{goal - total:,.0f} triệu`\n\n"
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
        await update.message.reply_text(f"✅ {m_id.upper()}: {str(result)}")
