
import numpy as np

try:
    from role.roles import Role
except ImportError:
    from script.role.roles import Role

class Platform(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_reward_width(self):
        return self.shape.get_reward_width()

    def get_state(self, window_size: tuple, velocity_scale: float = 20.0, **kwargs):
        """
        獲取正規化狀態。
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
    
    def reset(self):
        super().reset()


