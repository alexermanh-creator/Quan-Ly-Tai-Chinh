import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# Nạp tất cả module tự động
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

    # --- ƯU TIÊN 1: CÁC NÚT ĐIỀU HƯỚNG CHÍNH ---
    if text in ["🏠 Trang chủ", "❌ Hủy", "🏠 Home", "💼 Tài sản của bạn", "⬅️ Back"]:
        if 'dashboard' in modules:
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

    # --- ƯU TIÊN 2: TỰ ĐỘNG NHẬN DIỆN MODULE (PLUG & PLAY) ---
    for m_id, m_instance in modules.items():
        # Kiểm tra nếu module tự nhận lệnh (can_handle) hoặc khớp tên hiển thị
        info = m_instance.get_info()
        if (hasattr(m_instance, 'can_handle') and m_instance.can_handle(text)) or (info['name'] == text):
            result = m_instance.run(user_id, text if hasattr(m_instance, 'can_handle') and m_instance.can_handle(text) else None)
            await format_response(update, m_id, result)
            return

    # --- ƯU TIÊN 3: XỬ LÝ GIAO DỊCH VÀ CÁC LỆNH NHANH ---
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        
        if res == "EXIT_SIGNAL":
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

        if isinstance(res, str):
            # Nếu thành công hoặc hủy thì về Dashboard, nếu không thì hiện text thông báo
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
    
    # 1. Định dạng đặc biệt cho Dashboard
    if m_id == "dashboard" and isinstance(result, dict):
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
            f"🪙 Crypto: {result.get('crypto_val', '0đ')}\n\n"
            f"🏠 Bấm các nút dưới để quản lý chi tiết."
        )
        await update.message.reply_text(msg, reply_markup=main_markup, parse_mode="Markdown")
        return

    # 2. Xử lý tất cả các Module có trạng thái WIZARD (Crypto, Stock, Transaction...)
    if isinstance(result, dict) and result.get("status") == "wizard":
        msg_text = result.get("message", "Đang xử lý...")
        buttons = result.get("buttons", ["🏠 Trang chủ"])
        # Sắp xếp nút bấm 2 cột
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(msg_text, reply_markup=markup, parse_mode="Markdown")
        return

    # 3. Fallback cho kết quả dạng chuỗi hoặc lỗi
    final_text = result if isinstance(result, str) else "⚠️ Lỗi định dạng dữ liệu."
    await update.message.reply_text(final_text, reply_markup=main_markup, parse_mode="Markdown")
