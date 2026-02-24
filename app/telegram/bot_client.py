import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from backend.module_loader import load_all_modules

# 1. NẠP TẤT CẢ MODULE (DYNAMICS)
modules = load_all_modules()

# 2. MENU CHÍNH CỐ ĐỊNH
MAIN_MENU = [
    ["💼 Tài sản của bạn"],
    ["📊 Cổ phiếu", "🪙 Crypto"],
    ["🥇 Đầu tư khác", "➕ Giao dịch"],
    ["📜 Lịch sử", "🎯 Mục tiêu"],
    ["📈 Báo cáo", "⚙️ Cài đặt"],
    ["🤖 Trợ lý AI", "🏠 Trang chủ"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Khởi tạo bot"""
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text(
        "💼 *HỆ THỐNG QUẢN LÝ TÀI CHÍNH*\nSẵn sàng hỗ trợ bạn.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cơ chế Plug & Play: Điều hướng tin nhắn cho Module tự xử lý"""
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # --- TÌM MODULE CÓ THỂ XỬ LÝ TIN NHẮN NÀY ---
    target_module_id = None
    result = None

    # Ưu tiên các nút điều hướng quay về Dashboard trước
    if text in ["🏠 Trang chủ", "🏠 Home", "💼 Tài sản của bạn", "❌ Hủy"]:
        target_module_id = 'dashboard'
        result = modules['dashboard'].run(user_id)
    else:
        # Quét qua các module xem ai nhận lệnh này
        for m_id, m_instance in modules.items():
            # Module sẽ tự quyết định xem nó có handle được text này không (can_handle là hàm mới)
            if hasattr(m_instance, 'can_handle') and m_instance.can_handle(text):
                target_module_id = m_id
                result = m_instance.run(user_id, text)
                break
            # Trường hợp fallback cho các nút bấm Menu chính khớp tên Module
            elif m_instance.get_info()['name'] == text:
                target_module_id = m_id
                result = m_instance.run(user_id)
                break

    # --- HIỂN THỊ KẾT QUẢ ---
    if target_module_id and result:
        await format_response(update, target_module_id, result)
    else:
        # Nếu không ai nhận, thử đẩy vào Transaction (Parser nhanh)
        if 'transaction' in modules:
            res = modules['transaction'].run(user_id, text)
            if res:
                await format_response(update, 'transaction', res)
                return
        
        await update.message.reply_text("❓ Lệnh không hợp lệ. Vui lòng chọn Menu.")

async def format_response(update: Update, m_id: str, result: dict):
    """Giao diện hiển thị: Tuyệt đối tôn trọng Layout của Module"""
    main_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

    # 1. Nếu là Dashboard: Dùng layout đặc thù của Dashboard
    if m_id == "dashboard" and isinstance(result, dict):
        msg = (
            f"💼 *TÀI SẢN CỦA BẠN*\n"
            f"💰 Tổng: `{result.get('display_total', '0đ')}`\n"
            f"📈 Lãi: `{result.get('display_profit', '0đ')}` ({result.get('profit_percent', '0%')})\n\n"
            f"📊 Stock: {result.get('stock_val', '0đ')}\n"
            f"🪙 Crypto: {result.get('crypto_val', '0đ')}\n"
            f"🥇 Khác: {result.get('other_val', '0đ')}\n\n"
            f"🏦 Tiền mặt: {result.get('cash_val', '0đ')}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏠 Bấm các nút dưới để quản lý."
        )
        await update.message.reply_text(msg, reply_markup=main_markup, parse_mode="Markdown")

    # 2. Nếu Module trả về Wizard (Nút bấm): Hiển thị nguyên văn Message
    elif isinstance(result, dict) and result.get("status") == "wizard":
        buttons = result["buttons"]
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(result["message"], reply_markup=markup, parse_mode="Markdown")

    # 3. Trả về text đơn thuần (Thông báo thành công, lỗi...)
    else:
        # Nếu kết quả trả về là tín hiệu cần hiện lại Dashboard
        if any(x in str(result) for x in ["thành công", "chiết khấu"]):
            await update.message.reply_text(str(result), parse_mode="Markdown")
            db_res = modules['dashboard'].run(update.effective_user.id)
            await format_response(update, 'dashboard', db_res)
        else:
            await update.message.reply_text(str(result), reply_markup=main_markup, parse_mode="Markdown")
