import os
from backend.module_loader import load_all_modules

class FinancePlatform:
    def __init__(self):
        print("--- Khởi động Hệ thống Quản lý Tài chính Pro ---")
        # Khởi tạo bộ quét module
        self.modules = load_all_modules()
        print(f"--- Hệ thống sẵn sàng với {len(self.modules)} module ---")

    def execute_feature(self, module_id, user_id, data=None):
        """Hàm điều phối: Gọi module tương ứng khi có yêu cầu"""
        if module_id in self.modules:
            return self.modules[module_id].run(user_id, data)
        else:
            return "Lỗi: Module không tồn tại hoặc chưa được cắm vào."

if __name__ == "__main__":
    # Khởi tạo nền tảng
    app = FinancePlatform()
    
    # Ở giai đoạn này, danh sách module sẽ trống (0 module)
    # vì chúng ta chưa thêm module nào vào thư mục backend/modules.