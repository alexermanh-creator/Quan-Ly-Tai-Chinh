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
        ["🤖 Trợ lý AI", "🏠 Trang chủ"] # Đã đổi từ Home -> Trang chủ để đồng bộ
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "💼 *QUẢN LÝ TÀI SẢN VÀ ĐẦU TƯ*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ĐIỀU PHỐI TIN NHẮN: Trang chủ/Hủy -> Nút bấm -> Parser nhanh"""
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # 1. LOGIC QUAY VỀ TRANG CHỦ HOẶC HỦY (Ưu tiên cao nhất)
    if text in ["🏠 Trang chủ", "❌ Hủy", "🏠 Home"]:
        if 'dashboard' in modules:
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

    # 2. KIỂM TRA NÚT BẤM MENU (Ví dụ: [➕ Giao dịch])
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(user_id)
            await format_response(update, m_id, result)
            return

    # 3. KIỂM TRA LỆNH NHẬP TẮT HOẶC TIẾP TỤC WIZARD
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        
        if isinstance(res, str):
            # Nếu module báo về việc quay lại màn hình chính
            if "màn hình chính" in res or "Trang chủ" in res:
                result = modules['dashboard'].run(user_id)
                await update.message.reply_text(res)
                await format_response(update, 'dashboard', result)
            else:
                await update.message.reply_text(res)
            return
        
        elif isinstance(res, dict) and res.get("status") == "wizard":
            await format_response(update, 'transaction', res)
            return

    # 4. NẾU KHÔNG KHỚP GÌ CẢ
    await update.message.reply_text("❓ Tôi chưa hiểu lệnh này. Vui lòng chọn Menu hoặc nhập đúng cú pháp.")

async def format_response(update: Update, m_id: str, result: dict):
    """LAYOUT CHI TIẾT - Khôi phục Full Mục 10 và Wizard"""
    
    if m_id == "dashboard":
        total = result.get('total_assets', 0)
        goal = result.get('goal_value', 500)
        profit_loss = result.get('profit_loss', -31)
        profit_percent = result.get('profit_percent', -18)
        progress = result.get('goal_progress', 0)
        
        msg = (
            f"💼 *TÀI SẢN CỦA BẠN*\n"
            f"💰 Tổng: `{total:,.0f} triệu`\n"
            f"📈 Lãi: `{profit_loss} triệu` ({profit_percent}%)\n\n"
            f"📊 Stock: +12 triệu (+11%)\n"
            f"🪙 Crypto: -40 triệu (-63%)\n"
            f"🥇 Khác: -3 triệu (-6%)\n\n"
            f"🎯 Mục tiêu: `{goal} triệu`\n"
            f"Tiến độ: `{progress}%`\n"
            f"Còn thiếu: `{goal - total:,.0f} triệu`\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏠 Bấm các nút dưới để quản lý chi tiết."
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif isinstance(result, dict) and result.get("status") == "wizard":
        buttons = result["buttons"]
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(result["message"], reply_markup=reply_markup, parse_mode="Markdown")

    else:
        await update.message.reply_text(f"✅ Thông báo: {str(result)}")
