import os
import importlib.util
import sys

def load_all_modules():
    modules = {}
    # Lấy đường dẫn gốc của project
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    modules_dir = os.path.join(base_path, "backend", "modules")

    if not os.path.exists(modules_dir):
        print(f"❌ Thư mục không tồn tại: {modules_dir}")
        return modules

    for filename in os.listdir(modules_dir):
        if filename.endswith(".py") and filename != "interface.py" and not filename.startswith("__"):
            module_name = filename[:-3]
            file_path = os.path.join(modules_dir, filename)
            
            # Nạp module động
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            mod = importlib.util.module_from_spec(spec)
            
            try:
                spec.loader.exec_module(mod)
                if hasattr(mod, "Module"):
                    instance = mod.Module()
                    modules[instance.get_info()['id']] = instance
                    print(f"✅ Đã nạp Module: {instance.get_info()['name']}")
            except Exception as e:
                print(f"❌ Lỗi khi nạp module {filename}: {str(e)}")
                
    return modules
