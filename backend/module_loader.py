import importlib
import os
import inspect
from backend.interface import BaseModule

def load_all_modules():
    """Tự động quét và nạp tất cả module trong thư mục backend/modules"""
    modules = {}
    module_dir = os.path.join(os.path.dirname(__file__), "modules")
    
    # Kiểm tra nếu thư mục modules chưa tồn tại thì tạo mới
    if not os.path.exists(module_dir):
        os.makedirs(module_dir)
        return modules

    for filename in os.listdir(module_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            # Nạp module động
            module_spec = importlib.import_module(f"backend.modules.{module_name}")
            
            # Tìm class trong file đó có kế thừa từ BaseModule
            for name, obj in inspect.getmembers(module_spec):
                if inspect.isclass(obj) and issubclass(obj, BaseModule) and obj is not BaseModule:
                    instance = obj()
                    modules[instance.get_info()['id']] = instance
                    print(f"✅ Đã nạp Module: {instance.get_info()['name']}")
    
    return modules