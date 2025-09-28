

import json
import os
import time

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from game.role.player import Player

class Ability:

    def __init__(self, ability_name: str):

        self.ability_name = ability_name
        # 從 json 文件中加載對應數據
        print("Loading default ability configurations...")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(dir_path, './abilities_default_cfg.json')
        with open(config_path, 'r') as f:
            default_configs = json.load(f)
        
        player_configs = default_configs.get(self.ability_name)
        
        # Force 的意思是能力基於施加力來實現
        # Speed 的意思是能力基於直接修改速度來實現
        # Speed 和 Force 只能二選一
        # Cooldown 是該能力的冷卻時間，單位是秒
        if player_configs:
            self.force = player_configs.get("force")
            self.speed = player_configs.get("speed")
            self.cooldown = player_configs.get("cooldown")  # Default cooldown of 1 second
        else:
            raise ValueError(f"Default config for ability '{self.ability_name}' not found in {config_path}")

        self.last_used_time = 0  # Track the last time the ability was used

    def check_cooldowns(self) -> bool:
        """Check and update action cooldowns"""

        if (time.time() - self.last_used_time) > self.cooldown:
            self.last_used_time = time.time()
            return True
        return False
    
    def action(self, action_value, player: 'Player'):
        raise NotImplementedError(f"This method '{self.action.__name__}' should be overridden by subclasses.")
    
    def reset(self):
        """重設此能力的內部狀態，例如冷卻時間。"""
        self.last_used_time = 0
    
    def get_cooldown(self):
        return self.cooldown

    def get_last_used_time(self):
        return self.last_used_time