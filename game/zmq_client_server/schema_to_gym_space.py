import gymnasium as gym  # 如果是舊版 Ray/Gym，請使用 import gym
import numpy as np

def schema_to_gym_space(schema):
    """
    將自定義的 dict schema 遞歸轉換為 gymnasium.spaces 對象
    """
    # 情況 1: 節點包含具體的空間定義 ("type")
    if isinstance(schema, dict) and "type" in schema:
        space_type = schema["type"]
        
        if space_type == "box":
            return gym.spaces.Box(
                low=schema["range"][0],
                high=schema["range"][1],
                shape=tuple(schema["shape"]),
                dtype=np.dtype(schema["dtype"])
            )
            
        elif space_type == "discrete":
            return gym.spaces.Discrete(n=schema["n"])
            
        elif space_type == "dict":
            # 遞歸處理內部的 'spaces'
            nested_spaces = {
                key: schema_to_gym_space(val) 
                for key, val in schema["spaces"].items()
            }
            return gym.spaces.Dict(nested_spaces)
            
        else:
            raise ValueError(f"Unknown space type: {space_type}")

    # 情況 2: 根節點或容器 (沒有 "type" 鍵，例如最外層)
    elif isinstance(schema, dict):
        nested_spaces = {
            key: schema_to_gym_space(val) 
            for key, val in schema.items()
        }
        return gym.spaces.Dict(nested_spaces)
    
    else:
        raise ValueError(f"Invalid schema format: {schema}")