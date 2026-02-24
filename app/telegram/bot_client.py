import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# Tải tất cả module hiện có
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

    # --- 1. ĐIỀU HƯỚNG CHÍNH (QUAY VỀ DASHBOARD) ---
    if text in ["🏠 Trang chủ", "❌ Hủy", "🏠 Home", "💼 Tài sản của bạn", "⬅️ Back"]:
        if 'dashboard' in modules:
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return

    # --- 2. CƠ CHẾ PLUG & PLAY (DÀNH CHO STOCK, CRYPTO VÀ CÁC MODULE SAU NÀY) ---
    # Quét qua tất cả module để xem module nào "nhận" xử lý tin nhắn này
    for m_id, m_instance in modules.items():
        # Module tự nhận lệnh qua can_handle (nút bấm con, lệnh viết tay như price, del, gia, xoa)
        # Hoặc khớp chính xác tên Module trên Menu chính
        if (hasattr(m_instance, 'can_handle') and m_instance.can_handle(text)) or m_instance.get_info()['name'] == text:
            
            # Thực thi module (truyền text nếu module can_handle được lệnh đó)
            data_to_pass = text if (hasattr(m_instance, 'can_handle') and m_instance.can_handle(text)) else None
            result = m_instance.run(user_id, data_to_pass)
            
            # Nếu module trả về chuỗi văn bản (ví dụ thông báo thành công)
            if isinstance(result, str):
                await update.message.reply_text(result, parse_mode="Markdown")
                # Reload lại danh mục của chính module đó để cập nhật hiển thị
                refresh = m_instance.run(user_id)
                await format_response(update, m_id, refresh)
            else:
                # Nếu trả về dict (Wizard/Layout), hiển thị bình thường
                await format_response(update, m_id, result)
            return

    # --- 3. XỬ LÝ GIAO DỊCH NHANH (TRANSACTION) ---
    if 'transaction' in modules:
        res = modules['transaction'].run(user_id, text)
        if res == "EXIT_SIGNAL":
            result = modules['dashboard'].run(user_id)
            await format_response(update, 'dashboard', result)
            return
        
        if isinstance(res, str):
            await update.message.reply_text(res)
            # Nếu giao dịch thành công, quay về Dashboard
            if any(x in res for x in ["thành công", "Trang chủ", "hủy"]):
                await format_response(update, 'dashboard', modules['dashboard'].run(user_id))
            return
        elif isinstance(res, dict) and res.get("status") == "wizard":
            await format_response(update, 'transaction', res)
            return

    await update.message.reply_text("❓ Tôi chưa hiểu lệnh này. Hãy chọn Menu hoặc gõ lệnh nhanh.")

async def format_response(update: Update, m_id: str, result: dict):
    """Hàm hiển thị thống nhất - Giữ nguyên Layout từ module trả về"""
    main_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    
    # Render riêng cho Dashboard vì cấu trúc key phức tạp
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

    # Render cho các Module dạng Wizard (Nút bấm động)
    elif isinstance(result, dict) and result.get("status") == "wizard":
        buttons = result["buttons"]
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        # In nguyên văn message (giữ layout gạch ngang, xuống dòng của bạn)
        await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")
    
    # Trường hợp kết quả là text đơn thuần
    else:
        await update.message.reply_text(str(result), reply_markup=main_markup, parse_mode="Markdown")
