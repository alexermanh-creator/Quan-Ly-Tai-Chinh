import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# 1. NẠP TẤT CẢ MODULE CỦA HỆ THỐNG
modules = load_all_modules()

# 2. ĐỊNH NGHĨA MENU CHÍNH
MAIN_MENU = [
    ["💼 Tài sản của bạn"],
    ["📊 Cổ phiếu", "🪙 Crypto"],
    ["🥇 Đầu tư khác", "➕ Giao dịch"],
    ["📜 Lịch sử", "🎯 Mục tiêu"],
    ["📈 Báo cáo", "⚙️ Cài đặt"],
    ["🤖 Trợ lý AI", "🏠 Trang chủ"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start khởi tạo màn hình chính"""
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text(
        "💼 *QUẢN LÝ TÀI SẢN VÀ ĐẦU TƯ*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Điều hướng tin nhắn thông minh"""
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # A. LOGIC QUAY VỀ TRANG CHỦ HOẶC HỦY
    if text in ["🏠 Trang chủ", "❌ Hủy", "🏠 Home", "💼 Tài sản của bạn", "⬅️ Back"]:
        if 'dashboard' in modules:
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

    # B. XỬ LÝ NÚT BẤM TRONG MENU CON CỦA STOCK
    # Nếu đang ở trong Stock Module và bấm "➕ Giao dịch"
    if text == "➕ Giao dịch" and 'transaction' in modules:
        result = modules['transaction'].run(user_id)
        await format_response(update, 'transaction', result)
        return

    # C. ĐIỀU HƯỚNG THEO TÊN MODULE (DASHBOARD, STOCK, CRYPTO...)
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            result = m_instance.run(user_id)
            await format_response(update, m_id, result)
            return

    # D. XỬ LÝ CÁC LỆNH TRONG WIZARD HOẶC PARSER NHANH
    # Ưu tiên kiểm tra xem có phải lệnh của Stock Module (Cập nhật giá, Xóa mã...) không
    if 'stock' in modules:
        # Chuyển tiếp text vào stock module để kiểm tra lệnh con
        res_stock = modules['stock'].run(user_id, text)
        if isinstance(res_stock, dict) and res_stock.get("status") == "wizard":
             # Nếu text khớp với một lệnh trong Stock (VD: Cập nhật giá), nó sẽ trả về kết quả
             if text in ["🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã"]:
                 await format_response(update, 'stock', res_stock)
                 return

    # Cuối cùng mới chuyển vào Transaction Parser
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        if isinstance(res, str):
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
    """GIAO DIỆN HIỂN THỊ CHI TIẾT (MỤC 10 & STOCK MENU)"""
    main_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

    # NHÁNH 1: DASHBOARD CHÍNH
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

    # NHÁNH 2: MODULE CỔ PHIẾU (Xử lý cả String và Wizard Menu)
    elif m_id == "stock":
        if isinstance(result, dict) and result.get("status") == "wizard":
            buttons = result["buttons"]
            # Tạo layout 2 cột cho nút bấm
            keyboard = [buttons[i:i+2] for i in range(0, len(buttons)-1, 2)]
            # Dòng cuối là nút Back
            keyboard.append([buttons[-1]]) 
            markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(result, reply_markup=main_markup, parse_mode="Markdown")

    # NHÁNH 3: WIZARD GIAO DỊCH
    elif isinstance(result, dict) and result.get("status") == "wizard":
        buttons = result["buttons"]
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")
    
    else:
        await update.message.reply_text(f"✅ {str(result)}")
