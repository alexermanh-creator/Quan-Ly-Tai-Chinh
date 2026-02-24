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

    # A. ƯU TIÊN 1: LOGIC QUAY VỀ TRANG CHỦ / TÀI SẢN (NÚT MENU CHÍNH)
    # Chúng ta bắt chính xác các text này để không cho nó trôi xuống module khác
    if text in ["🏠 Trang chủ", "❌ Hủy", "🏠 Home", "💼 Tài sản của bạn", "⬅️ Back"]:
        if 'dashboard' in modules:
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

    # B. ƯU TIÊN 2: LỆNH NHẬP TAY ĐẶC BIỆT (STOCK: xoa, gia...)
    if text.lower().startswith("xoa ") or text.lower().startswith("gia "):
        if 'stock' in modules:
            res_stock = modules['stock'].run(user_id, text)
            if isinstance(res_stock, str):
                await update.message.reply_text(res_stock)
                refresh_pf = modules['stock'].run(user_id)
                await format_response(update, 'stock', refresh_pf)
                return

    # C. ƯU TIÊN 3: CÁC NÚT BẤM MENU KHÁC (Cổ phiếu, Crypto, Giao dịch...)
    # Kiểm tra xem text có trùng với tên Module nào không
    for m_id, m_instance in modules.items():
        if m_instance.get_info()['name'] == text:
            # Nếu là nút "➕ Giao dịch", nó sẽ hiện menu wizard của giao dịch
            result = m_instance.run(user_id)
            await format_response(update, m_id, result)
            return

    # D. ƯU TIÊN 4: LỆNH WIZARD ĐANG DANG DỞ TRONG STOCK
    if 'stock' in modules:
        res_stock = modules['stock'].run(user_id, text)
        if isinstance(res_stock, dict) and res_stock.get("status") == "wizard":
             if text in ["🔄 Cập nhật giá", "📈 Báo cáo nhóm", "❌ Xóa mã"]:
                 await format_response(update, 'stock', res_stock)
                 return

    # E. CUỐI CÙNG: MỚI CHUYỂN VÀO TRANSACTION PARSER (Lệnh nhanh như "nap 1ty" hoặc "btc 1 70000")
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        if isinstance(res, str):
            # Nếu kết quả trả về có từ khóa báo thành công/quay về, hiện lại Dashboard
            if any(x in res for x in ["Trang chủ", "thành công", "hủy", "chiết khấu"]):
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
    """GIAO DIỆN HIỂN THỊ CHI TIẾT"""
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

    elif m_id == "stock":
        if isinstance(result, dict) and result.get("status") == "wizard":
            buttons = result["buttons"]
            keyboard = [buttons[i:i+2] for i in range(0, len(buttons)-1, 2)]
            keyboard.append([buttons[-1]]) 
            markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(result, reply_markup=main_markup, parse_mode="Markdown")

    elif isinstance(result, dict) and result.get("status") == "wizard":
        buttons = result["buttons"]
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")
    
    else:
        await update.message.reply_text(f"✅ {str(result)}")
