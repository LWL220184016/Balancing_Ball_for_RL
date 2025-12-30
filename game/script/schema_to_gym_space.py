import gymnasium as gym
import numpy as np

def schema_to_gym_space(schema: dict):
    """
    將 schema 轉換為 gymnasium.spaces.Dict。
    直接使用技能名稱（Top-level key）作為 Gym Space 的 Key。
    """
    spaces = {}

    for skill_name, config in schema.items():
        space_type = config.get("type")

        if space_type == "box":
            spaces[skill_name] = gym.spaces.Box(
                low=config["range"][0],
                high=config["range"][1],
                shape=tuple(config["shape"]),
                dtype=np.dtype(config.get("dtype", "float32"))
            )
            
        elif space_type == "discrete":
            spaces[skill_name] = gym.spaces.Discrete(n=config["n"])
            
        # 如果未來仍有巢狀需求，可在此擴充，目前根據需求僅處理單層
        else:
            raise ValueError(f"Unknown space type: {space_type} for skill: {skill_name}")

    return gym.spaces.Dict(spaces)

# 測試用例
if __name__ == "__main__":
    example_schema = {
        'Move_topdown_viewing_angle': {
            'type': 'box', 
            'dtype': 'float32', 
            'shape': [2], 
            'range': [-1.0, 1.0], 
            'description': 'Multiply the output by Force for moving'
        }, 
        'Turning_topdown_viewing_angle': {
            'type': 'box', 
            'dtype': 'float32', 
            'shape': [1], 
            'range': [-1.0, 1.0], 
            'description': 'Multiply the output by 180 degrees for rotation'
        }, 
        'Shoot': {
            'type': 'discrete', 
            'dtype': 'int64', 
            'n': 2
        }
    }

    action_space = schema_to_gym_space(example_schema)
    print(action_space)
    
    # 測試隨機採樣
    print("Sample action:", action_space.sample())