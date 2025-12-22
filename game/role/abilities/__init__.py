import os
import glob
import importlib

# 找出該目錄下所有的 .py 檔案名稱 (不含 .py 副檔名)
# 例如: ['ability', 'move', 'jump']
module_names = [
    os.path.basename(f)[:-3] 
    for f in glob.glob(os.path.join(os.path.dirname(__file__), "*.py")) 
    if not f.endswith('__init__.py')
]
msg = f"Found ability modules: {module_names}"
print(f"\n\033[38;5;222m {msg}\033[0m")

# __all__ 將用來存放要匯出的類別名稱 (例如 'Move', 'Jump')
__all__ = []

# 遍歷所有找到的模組名稱
for module_name in module_names:
    # 遵循命名約定：將模組名 'dash' 轉換為類別名 'Dash' (首字母大寫)
    class_name = module_name.capitalize()
    
    # 動態導入模組 (例如 from . import dash)
    module = importlib.import_module(f".{module_name}", __name__)
    
    # 檢查模組中是否存在對應的類別
    if hasattr(module, class_name):
        # 將類別物件賦值給目前 __init__.py 的全域變數
        # 這一步等同於手動寫 from .dash import Dash
        globals()[class_name] = getattr(module, class_name)
        
        # 將類別名稱加入 __all__ 列表，以便 `import *` 可以匯出它
        __all__.append(class_name)
        print(f"\033[38;5;34m Loaded ability class: {class_name} from module: {module_name} \033[0m")