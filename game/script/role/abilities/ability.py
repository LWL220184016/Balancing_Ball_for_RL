import json
import os

from abc import ABC, abstractmethod
from role.abilities.key_mapping import KeyMapping
from script.game_config import GameConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from script.role.player import Player

class Ability(ABC):
    _default_configs = None  # 用於緩存配置的類變量
    _fps = None  # 用於儲存 FPS 的類變量

    @abstractmethod
    def __init__(self, ability_name: str):
        self.ability_name = ability_name
        self.ability_generated_object_name = None
        self.ability_generated_object_config = None
        
        # 確保只被初始化一次
        if Ability._default_configs is None:
            Ability._initialize_class_assets()
        
        abilities_configs = Ability._default_configs.get(self.ability_name)

        if Ability._fps is None:
            Ability._fps = GameConfig.FPS  # Default to 60 FPS if not specified

        # Force 的意思是能力基於施加力來實現
        # Speed 的意思是能力基於直接修改速度來實現
        # Speed 和 Force 只能二選一
        # Cooldown 是該能力的冷卻時間，單位是秒
        if abilities_configs:
            self.force = abilities_configs.get("force")
            self.speed = abilities_configs.get("speed")
            self.cooldown = abilities_configs.get("cooldown") * Ability._fps  # Default cooldown of 1 second
            self.control_keys = abilities_configs.get("key")
            self.action_space = abilities_configs.get("action_space")
        else:
            # 即使配置已加載，仍需處理找不到特定能力配置的情況
            dir_path = os.path.dirname(os.path.realpath(__file__))
            config_path = os.path.join(dir_path, './abilities_default_cfg.json')
            raise ValueError(f"Default config for ability '{self.ability_name}' not found in {config_path}")

        self.last_used_step = None  # Track the last time the ability was used

    @abstractmethod
    def action(self, action_value, player: 'Player'):
        raise NotImplementedError(f"This method '{self.action.__name__}' should be overridden by subclasses.")

    @abstractmethod
    def human_control_interface(self, keyboard_keys, mouse_buttons, mouse_position):
        """
        提供給 HumanControl 使用的接口方法，讓玩家能夠通過鍵盤/滑鼠輸入來控制此能力。
        這個方法目的在於將玩家的輸入轉換為能力所需的 action_value。
        每個能力需要的轉換方式都不一樣，
        函數會返回 action_value 而不是直接呼叫 action 因為 action 需要在遊戲主循環中被呼叫，
        而 human_control_interface 只是負責處理輸入並產生 action_value。

        子類需要覆寫此方法以實現自定義的輸入邏輯。
        """
        pass
    
    @abstractmethod
    def reset(self):
        """重設此能力的內部狀態，例如冷卻時間。"""
        self.last_used_step = None

    def _is_pressed(self, kb_list, ms_list, kb_state, ms_state):
        """高效檢查一組按鍵中是否有任何一個被按下"""
        for k in kb_list:
            if kb_state[k]: return True
        for m in ms_list:
            if ms_state[m]: return True
        return False
    
    @classmethod
    def _initialize_class_assets(cls):
        """一次性初始化配置、按鍵映射與動態 Action 類"""
        print("Initializing Global Ability Assets...")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(dir_path, './abilities_default_cfg.json')
        
        with open(config_path, 'r') as f:
            raw_data = json.load(f)
        
        # 處理按鍵映射 (In-place)
        for name, cfg in raw_data.items():
            if "key" in cfg:
                cfg["key"] = KeyMapping.get(cfg["key"])
        
        cls._default_configs = raw_data
        cls._fps = GameConfig.FPS

    def check_is_ready(self, current_step: int) -> bool:
        """Check and update action cooldowns"""
        if self.last_used_step is None or (current_step - self.last_used_step) >= self.cooldown:
            return True
        return False
        
    def get_cooldown(self):
        return self.cooldown

    def get_action_spec(self) -> dict:
        """
        返回該能力的動作空間規格說明 (Action Space Specification)。
        
        此規格定義了客戶端（人類或 AI 代理）在調用此能力時，必須提供的 `action_value` 
        數據結構。此格式直接兼容 Gymnasium (OpenAI Gym) 的空間定義，
        並可由 Ray RLlib 自動解析為模型輸出頭。

        Returns:
            dict: 包含動作空間定義的字典。結構如下：
                {
                    "type": str,      # 空間類型，例如 "dict", "box", "discrete"
                    "spaces": dict,    # 當 type 為 "dict" 時，定義子空間的映射
                    "description": str # (可選) 該能力的物理意義描述
                }

        Data Structure Detail (Example: Composite Ability):
            若返回 "type": "dict"，`action_value` 應為一個字典，包含以下子項：
            
            1. "direction" (Box Space):
                - 類型: 連續型數值向量 (Continuous)。
                - 物理意義: 控制能力施放的方向。
                - 數值範圍: [-3.14, 3.14] (弧度制，對應 -180° 到 180°)。
                - AI 建議: RL 模型將使用高斯分佈 (Gaussian) 進行採樣。

            2. "action" (Discrete Space):
                - 類型: 離散型類別 (Categorical)。
                - 物理意義: 觸發開關。0 代表不執行，1 代表執行/觸發。
                - 選項數量 (n): 2。
                - AI 建議: RL 模型將使用分類分佈 (Categorical/Softmax) 進行採樣。

        Example Output Mapping:
            >>> spec = ability.get_action_spec()
            >>> print(spec["spaces"]["direction"]["range"])
            [-3.14, 3.14]

        Note:
            在 Ray RLlib 環境中，此規格將被轉換為 `gym.spaces.Dict`，
            確保策略網絡 (Policy Network) 的輸出維度與遊戲邏輯完美對齊。
        """
        return self.action_space

    def get_last_used_step(self):
        return self.last_used_step
    
    def get_name(self):
        return self.__class__.__name__
    
    def set_last_used_step(self, step: int):
        self.last_used_step = step

    