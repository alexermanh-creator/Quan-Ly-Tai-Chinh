import os
import importlib.util

def load_all_modules():
    modules = {}
    # Đường dẫn tuyệt đối đến thư mục modules
    base_path = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.join(base_path, "modules")

    for filename in os.listdir(modules_dir):
        if filename.endswith(".py") and filename != "interface.py" and not filename.startswith("__"):
            module_name = filename[:-3]
            file_path = os.path.join(modules_dir, filename)
            
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            if hasattr(mod, "Module"):
                instance = mod.Module()
                modules[instance.get_info()['id']] = instance
                # Dòng Log này rất quan trọng để bạn kiểm tra trên Railway
                print(f"✅ Đã nạp Module: {instance.get_info()['name']}")
                
    return modules
