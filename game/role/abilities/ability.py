import json
import os

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from game.role.player import Player

class Ability:
    _default_configs = None  # 用於緩存配置的類變量
    _fps = None  # 用於儲存 FPS 的類變量

    def __init__(self, ability_name: str):

        self.ability_name = ability_name
        # 檢查配置是否已加載，如果沒有則加載一次
        if Ability._default_configs is None:
            print("Loading default ability configurations for the first time...")
            dir_path = os.path.dirname(os.path.realpath(__file__))
            config_path = os.path.join(dir_path, './abilities_default_cfg.json')
            with open(config_path, 'r') as f:
                Ability._default_configs = json.load(f)
        
        abilities_configs = Ability._default_configs.get(self.ability_name)

        if Ability._fps is None:
            from RL.levels.level3.config import model_config  # Adjust the import path as necessary
            Ability._fps = model_config.fps  # Default to 60 FPS if not specified

        # Force 的意思是能力基於施加力來實現
        # Speed 的意思是能力基於直接修改速度來實現
        # Speed 和 Force 只能二選一
        # Cooldown 是該能力的冷卻時間，單位是秒
        if abilities_configs:
            self.force = abilities_configs.get("force")
            self.speed = abilities_configs.get("speed")
            self.cooldown = abilities_configs.get("cooldown") * Ability._fps  # Default cooldown of 1 second
        else:
            # 即使配置已加載，仍需處理找不到特定能力配置的情況
            dir_path = os.path.dirname(os.path.realpath(__file__))
            config_path = os.path.join(dir_path, './abilities_default_cfg.json')
            raise ValueError(f"Default config for ability '{self.ability_name}' not found in {config_path}")

        self.last_used_step = 0  # Track the last time the ability was used

    def check_cooldowns(self, current_step: int) -> bool:
        """Check and update action cooldowns"""

        if (current_step - self.last_used_step) > self.cooldown:
            self.last_used_step = current_step
            return True
        return False
    
    def action(self, action_value, player: 'Player'):
        raise NotImplementedError(f"This method '{self.action.__name__}' should be overridden by subclasses.")
    
    def reset(self):
        """重設此能力的內部狀態，例如冷卻時間。"""
        self.last_used_step = 0
    
    def get_cooldown(self):
        return self.cooldown

    def get_last_used_step(self):
        return self.last_used_step