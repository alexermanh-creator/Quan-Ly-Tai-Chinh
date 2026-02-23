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
    """LAYOUT CHI TIẾT - Fix lỗi hiển thị Wizard"""
    # Nếu là Dashboard thì hiện bảng tổng kết (Mục 10)
    if m_id == "dashboard":
        total = result.get('total_assets', 0)
        goal = result.get('goal_value', 500)
        msg = (
            f"💼 *TÀI SẢN CỦA BẠN*\n"
            f"💰 Tổng: `{total:,.0f} triệu`\n"
            f"📈 Lãi: `{result.get('profit_loss', 0)} triệu` ({result.get('profit_percent', 0)}%)\n\n"
            f"🎯 Mục tiêu: `{goal} triệu`\n"
            f"Tiến độ: `{result.get('goal_progress', 0)}%`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 Tiền mặt: {result.get('cash', 0)} triệu"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    # NẾU LÀ TRANSACTION VÀ CẦN HIỆN NÚT BẤM (Fix lỗi bạn đang gặp)
    elif isinstance(result, dict) and result.get("status") == "wizard":
        from telegram import ReplyKeyboardMarkup
        keyboard = [result["buttons"][i:i+2] for i in range(0, len(result["buttons"]), 2)]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(result["message"], reply_markup=reply_markup)

    else:
        # Hiển thị mặc định cho các trường hợp khác
        await update.message.reply_text(f"✅ {m_id.upper()}: {str(result)}")

