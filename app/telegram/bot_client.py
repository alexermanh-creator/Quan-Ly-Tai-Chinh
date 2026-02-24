async def format_response(update: Update, m_id: str, result: dict):
    # Khởi tạo Menu chính để luôn hiển thị dưới tin nhắn
    main_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    
    # TRƯỜNG HỢP 1: DASHBOARD (Giữ nguyên logic của bạn)
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

    # TRƯỜNG HỢP 2: TẤT CẢ CÁC MODULE KHÁC (Crypto, Stock, Transaction...)
    # Nếu kết quả trả về là một Wizard (có tin nhắn và nút bấm riêng)
    if isinstance(result, dict) and result.get("status") == "wizard":
        msg_text = result.get("message", "Đang xử lý...")
        btns = result.get("buttons", ["🏠 Trang chủ"])
        
        # Sắp xếp nút bấm 2 cột tự động
        keyboard = [btns[i:i+2] for i in range(0, len(btns), 2)]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(msg_text, reply_markup=markup, parse_mode="Markdown")
        return

    # TRƯỜNG HỢP 3: FALLBACK (Nếu chỉ trả về chuỗi văn bản bình thường)
    final_text = result if isinstance(result, str) else "⚠️ Module không trả về dữ liệu hợp lệ."
    await update.message.reply_text(final_text, reply_markup=main_markup, parse_mode="Markdown")
