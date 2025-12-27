from typing import Type # 記得導入 Type

class FrozenClass(type):
    def __setattr__(cls, key, value):
        # 如果屬性已經存在（且不是內部的私有變量），則禁止修改
        if hasattr(cls, key) and not key.startswith("_"):
            raise AttributeError(f"GameConfig 屬性 '{key}' 已鎖定，不可二次修改")
        super().__setattr__(key, value)

class GameConfig(metaclass=FrozenClass):
    # 僅定義類型註解（Type Hinting），不賦予初始值
    # 這樣在調用 init_from_configs 之前，存取這些變數會直接報錯 (AttributeError)
    SCREEN_WIDTH: int
    SCREEN_HEIGHT: int
    COLLISION_TYPES: dict
    ABILITIES_OBJECTS_CONFIGS: dict
    GRAVITY: tuple
    DAMPING: float
    FPS: int
    PLAYER_NUM: int
    ACTION_SPACE_CONFIG: dict

    @classmethod
    def init_from_configs(cls, env_cfg: dict, collision_cfg: dict, abilities_objects_configs: dict = {}):
        """
        從配置字典初始化。如果缺少任何必要參數，直接拋出異常。
        """
        required_env_keys = ["window_x", "window_y", "gravity", "damping"]
        for key in required_env_keys:
            if key not in env_cfg:
                raise ValueError(f"配置錯誤：在 environment_configs 中找不到必要參數 '{key}'")

        if not collision_cfg:
            raise ValueError("配置錯誤：collision_type 字典為空或未定義")
        
        try:
            cls.SCREEN_WIDTH = int(env_cfg["window_x"])
            cls.SCREEN_HEIGHT = int(env_cfg["window_y"])
            cls.GRAVITY = tuple(env_cfg["gravity"])
            cls.DAMPING = float(env_cfg["damping"])
            cls.FPS = float(env_cfg["fps"])
            cls.COLLISION_TYPES = collision_cfg
            cls.ABILITIES_OBJECTS_CONFIGS = abilities_objects_configs
        except (TypeError, ValueError) as e:
            raise ValueError(f"配置錯誤：參數類型不正確或格式錯誤。細節: {e}")

        print(f"[Config] 全域參數載入成功：{cls.SCREEN_WIDTH}x{cls.SCREEN_HEIGHT}, Gravity: {cls.GRAVITY}")

    @classmethod
    def scale_x(cls, ratio: float) -> float:
        # 如果未初始化，此處會觸發 AttributeError: type object 'GameConfig' has no attribute 'SCREEN_WIDTH'
        return cls.SCREEN_WIDTH * ratio

    @classmethod
    def scale_y(cls, ratio: float) -> float:
        return cls.SCREEN_HEIGHT * ratio

    @classmethod
    def get_collision_type(cls, name: str) -> int:
        if name not in cls.COLLISION_TYPES:
            raise KeyError(f"配置錯誤：在 collision_type 中找不到名為 '{name}' 的定義")
        return cls.COLLISION_TYPES[name]
        