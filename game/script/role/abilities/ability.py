import json
import os

from abc import ABC, abstractmethod
from role.abilities.key_mapping import KeyMapping
from script.game_config import GameConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from script.role.player import Player

class Ability(ABC):
    _default_configs = None  # 用於緩存配置的類變量
    _fps = None  # 用於儲存 FPS 的類變量

    @abstractmethod
    def __init__(self, ability_name: str):
        self.ability_name = ability_name
        
        if Ability._default_configs is None:
            print("Loading and mapping configurations...")
            dir_path = os.path.dirname(os.path.realpath(__file__))
            config_path = os.path.join(dir_path, './abilities_default_cfg.json')
            with open(config_path, 'r') as f:
                raw_data = json.load(f)
            
            for name, cfg in raw_data.items():
                if "key" in cfg:
                    # 直接修改類變量中的內容，將字符串替換為具體數值/對象
                    cfg["key"] = KeyMapping.get(cfg["key"])
            
            Ability._default_configs = raw_data
        
        # 之後的實例直接讀取已經映射好的數據
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
        else:
            # 即使配置已加載，仍需處理找不到特定能力配置的情況
            dir_path = os.path.dirname(os.path.realpath(__file__))
            config_path = os.path.join(dir_path, './abilities_default_cfg.json')
            raise ValueError(f"Default config for ability '{self.ability_name}' not found in {config_path}")

        self.last_used_step = None  # Track the last time the ability was used

    def check_is_ready(self, current_step: int) -> bool:
        """Check and update action cooldowns"""
        if self.last_used_step is None or (current_step - self.last_used_step) >= self.cooldown:
            return True
        return False
        
    @abstractmethod
    def action(self, action_value, player: 'Player'):
        raise NotImplementedError(f"This method '{self.action.__name__}' should be overridden by subclasses.")

    @abstractmethod
    def human_control_interface(self, keyboard_keys, mouse_buttons):
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
    
    def get_cooldown(self):
        return self.cooldown

    def get_last_used_step(self):
        return self.last_used_step
    
    def get_name(self):
        return self.__class__.__name__
    
    def set_last_used_step(self, step: int):
        self.last_used_step = step

    