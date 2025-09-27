
import numpy as np
from role.roles import Role
from role.shapes.shape import Shape

class Platform(Role):
    def __init__(self, shape: Shape, platform_color: tuple, action_params: dict, action_cooldown: dict):
        super().__init__(shape, platform_color, action_params, action_cooldown)
        self.platform_color = platform_color
        self.action_cooldown = action_cooldown  # Dictionary of action cooldowns
        self.action_params = action_params  # Dictionary of action parameters
        self.last_action_time = {action: 0 for action in action_cooldown}  # Track last action time for each action

    def move(self, direction):
        raise NotImplementedError(f"This method '{self.move.__name__}' not implemented.")

    def perform_action(self, players_action):
        raise NotImplementedError(f"This method '{self.perform_action.__name__}' not implemented.")
    
    def get_reward_width(self):
        return self.shape.get_reward_width()

    def get_state(self, window_size, velocity_scale=20.0, **kwargs):
        """
        獲取玩家的正規化狀態。
        使用 tanh 函數來處理沒有固定上限的速度。
        velocity_scale: 用於調整速度的靈敏度。
        """
        # 首先，從父類獲取基本狀態（位置、技能冷卻等）
        state = super().get_state(window_size=window_size, **kwargs)

        # 接著，添加正規化的速度
        angular_v = self.get_angular_velocity()

        # 使用 tanh 進行正規化，velocity_scale 是一個超參數，用於調整靈敏度
        norm_angular_v = np.tanh(angular_v / velocity_scale)

        state.extend([norm_angular_v])

        return state
    
    def reset(self, space):
        super().reset(space)