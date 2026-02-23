import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# Nạp tất cả module
modules = load_all_modules()

# Định nghĩa bộ Menu chính để dùng chung (Tránh lặp code)
MAIN_MENU = [
    ["💼 Tài sản của bạn"],
    ["📊 Cổ phiếu", "🪙 Crypto"],
    ["🥇 Khác", "➕ Giao dịch"],
    ["📜 Lịch sử", "🎯 Mục tiêu"],
    ["📈 Báo cáo", "⚙️ Cài đặt"],
    ["🤖 Trợ lý AI", "🏠 Trang chủ"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Khởi tạo Bot"""
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text(
        "💼 *QUẢN LÝ TÀI SẢN VÀ ĐẦU TƯ*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # 1. LOGIC QUAY VỀ TRANG CHỦ / HỦY -> HIỆN DASHBOARD + MENU CHÍNH
    if text in ["🏠 Trang chủ", "❌ Hủy", "🏠 Home", "💼 Tài sản của bạn"]:
        if 'dashboard' in modules:
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

    # 2. KIỂM TRA NÚT BẤM MENU
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(user_id)
            await format_response(update, m_id, result)
            return

    # 3. TIẾP TỤC WIZARD HOẶC PARSER
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        if isinstance(res, str):
            if "thành công" in res or "hủy" in res:
                # Sau khi xong việc, tự động hiện lại Dashboard cho tiện
                result = modules['dashboard'].run(user_id)
                await update.message.reply_text(res)
                await format_response(update, 'dashboard', result)
            else:
                await update.message.reply_text(res)
            return
        elif isinstance(res, dict) and res.get("status") == "wizard":
            await format_response(update, 'transaction', res)
            return

    await update.message.reply_text("❓ Tôi chưa hiểu lệnh này.")

async def format_response(update: Update, m_id: str, result: dict):
    # Luôn đính kèm Menu chính khi trả về Dashboard
    main_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

    if m_id == "dashboard":
        total = result.get('total_assets', 0)
        goal = result.get('goal_value', 500)
        
        msg = (
            f"💼 *TÀI SẢN CỦA BẠN*\n"
            f"💰 Tổng: `{total:,.0f} triệu`\n"
            f"📈 Lãi: `{result.get('profit_loss', -31)} triệu` ({result.get('profit_percent', -18)}%)\n\n"
            
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
        await update.message.reply_text(msg, reply_markup=main_markup, parse_mode="Markdown")

    elif isinstance(result, dict) and result.get("status") == "wizard":
        buttons = result["buttons"]
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")
