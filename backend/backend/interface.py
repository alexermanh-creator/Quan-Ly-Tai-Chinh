from abc import ABC, abstractmethod

class BaseModule(ABC):
    """
    Đây là Interface chuẩn. 
    Bất kỳ module nào 'cắm' vào hệ thống cũng phải có 2 hàm này.
    """
    
    @abstractmethod
    def get_info(self):
        """Trả về tên và mô tả của module"""
        pass

    @abstractmethod
    def run(self, user_id, data=None):
        """Hàm thực thi chính của module"""
        pass