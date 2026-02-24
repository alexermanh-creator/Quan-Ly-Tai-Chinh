import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

modules = load_all_modules()

MAIN_MENU = [
    ["💼 Tài sản của bạn"],
    ["📊 Cổ phiếu", "🪙 Crypto"],
    ["🥇 Đầu tư khác", "➕ Giao dịch"],
    ["📜 Lịch sử", "🎯 Mục tiêu"],
    ["📈 Báo cáo", "⚙️ Cài đặt"],
    ["🤖 Trợ lý AI", "🏠 Trang chủ"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("💼 *QUẢN LÝ TÀI SẢN VÀ ĐẦU TƯ*", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # --- ƯU TIÊN 1: CÁC NÚT ĐIỀU HƯỚNG CHÍNH (LUÔN PHẢI KIỂM TRA ĐẦU TIÊN) ---
    if text in ["🏠 Trang chủ", "❌ Hủy", "🏠 Home", "💼 Tài sản của bạn", "⬅️ Back"]:
        if 'dashboard' in modules:
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

    # --- ƯU TIÊN 2: LỆNH NHẬP TAY ĐẶC BIỆT CỦA STOCK ---
    if text.lower().startswith(("xoa ", "gia ")):
        if 'stock' in modules:
            res_stock = modules['stock'].run(user_id, text)
            if isinstance(res_stock, str):
                await update.message.reply_text(res_stock)
                refresh_pf = modules['stock'].run(user_id)
                await format_response(update, 'stock', refresh_pf)
                return

    # --- ƯU TIÊN 3: CÁC NÚT BẤM MENU CHÍNH ---
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(user_id)
            await format_response(update, m_id, result)
            return

    # --- ƯU TIÊN 4: XỬ LÝ GIAO DỊCH (WIZARD & PARSER) ---
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        
        # Nếu Transaction trả về tín hiệu thoát
        if res == "EXIT_SIGNAL":
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

        if isinstance(res, str):
            # Nếu thành công, hiện lại Dashboard
            if any(x in res for x in ["Trang chủ", "thành công", "hủy"]):
                result = modules['dashboard'].run(user_id)
                await update.message.reply_text(res)
                await format_response(update, 'dashboard', result)
            else:
                await update.message.reply_text(res)
            return
        elif isinstance(res, dict) and res.get("status") == "wizard":
            await format_response(update, 'transaction', res)
            return

    await update.message.reply_text("❓ Tôi chưa hiểu lệnh này. Hãy chọn Menu hoặc nhập lệnh nhanh.")

async def format_response(update: Update, m_id: str, result: dict):
    main_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    if m_id == "dashboard":
        msg = (
            f"💼 *TÀI SẢN CỦA BẠN*\n"
            f"💰 Tổng: `{result.get('display_total', '0đ')}`\n"
            f"📈 Lãi: `{result.get('display_profit', '0đ')}` ({result.get('profit_percent', '0%')})\n\n"
            f"📊 Stock: {result.get('stock_val', '0đ')}\n"
            f"🪙 Crypto: {result.get('crypto_val', '0đ')}\n"
            f"🥇 Khác: {result.get('other_val', '0đ')}\n\n"
            f"🎯 Mục tiêu: `{result.get('goal_display', '500 triệu')}`\n"
            f"Tiến độ: `{result.get('goal_progress', 0):,.1f}%`\n"
            f"Còn thiếu: `{result.get('remain_display', '0đ')}`\n\n"
            f"⬆️ Tổng nạp: {result.get('total_in', '0đ')}\n"
            f"⬇️ Tổng rút: {result.get('total_out', '0đ')}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 Tiền mặt: {result.get('cash_val', '0đ')}\n"
            f"📊 Cổ phiếu: {result.get('stock_val', '0đ')}\n"
            f"🪙 Crypto: {result.get('crypto_val', '0đ')}\n"
            f"🥇 Khác: {result.get('other_val', '0đ')}\n\n"
            f"🏠 Bấm các nút dưới để quản lý chi tiết."
        )
        await update.message.reply_text(msg, reply_markup=main_markup, parse_mode="Markdown")
    elif isinstance(result, dict) and result.get("status") == "wizard":
        buttons = result["buttons"]
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(str(result), reply_markup=main_markup, parse_mode="Markdown")
