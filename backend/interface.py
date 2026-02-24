from abc import ABC, abstractmethod

class BaseModule(ABC):
    @abstractmethod
    def get_info(self):
        """Trả về ID và Tên module"""
        pass

    @abstractmethod
    def run(self, user_id, data=None):
        """Hàm thực thi chính"""
        pass

    def can_handle(self, text):
        """
        Mặc định trả về False. 
        Các module sẽ override hàm này để tự nhận lệnh (ví dụ: nút bấm hoặc lệnh gia/xoa).
        """
        return False
