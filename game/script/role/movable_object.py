
try:
    from role.roles import Role
except ImportError:
    from script.role.roles import Role

class MovableObject(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_state(self, window_size: tuple, velocity_scale: float = 20.0, **kwargs):
        """
        獲取正規化狀態。
        使用 tanh 函數來處理沒有固定上限的速度。
        velocity_scale: 用於調整速度的靈敏度。
        """
        # 從父類獲取基本狀態（位置、技能冷卻等）
        state = super().get_state(window_size=window_size, velocity_scale=velocity_scale, **kwargs)

        return state

    def reset(self):

        super().reset()


