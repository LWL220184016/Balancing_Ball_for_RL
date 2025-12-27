import json
from typing import NamedTuple, Any, List, Type

def create_dynamic_tuple(class_name: str, field_names: List[str]) -> Type[tuple]:
    """
    通用函數：根據傳入的字符串列表創建帶默認值(None)的 NamedTuple 
    """
    
    # 1. 處理屬性名：轉為小寫並指定類型為 Any
    # 這裡我們讓它變成 (name, type) 的元組列表
    fields = [(name.lower(), Any) for name in field_names]
    
    # 2. 使用 NamedTuple 的動態 API 創建類 
    # 就像變魔術一樣生成一個新類
    DynamicClass = NamedTuple(class_name, fields)
    
    # 3. 設置默認值為 None 
    # 這樣實例化時就可以偷懶不填所有參數啦，沒填的自動變成 None
    DynamicClass.__new__.__defaults__ = (None,) * len(fields)
    
    return DynamicClass

ability_list = ["Move", "Jump", "Shoot", "Dance"] 

# 創建類！ 
PlayerAction = create_dynamic_tuple('PlayerAction', ability_list)

# --- 測試一下 ---
# 試試看只傳入部分參數，其他的會自動變成 None 
action = PlayerAction(move=100, jump=True)

print(f"類名: {action.__class__.__name__}")
print(f"Move: {action.move}")   # 應該是 100
print(f"Jump: {action.jump}")   # 應該是 True
print(f"Shoot: {action.shoot}") # 應該是 None 
print(f"完整對象: {action}")