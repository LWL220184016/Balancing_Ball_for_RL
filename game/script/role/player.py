import pymunk

try:
    from role.roles import Role
except ImportError:
    from script.role.roles import Role

class Player(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_on_ground = False
        self.last_direction = None  # 用於追踪玩家上一次移動的方向
        self.direction_count = 0  # 用於追踪玩家是否一直向同一方向移動
        self.reward_per_step = 0  # 每一步的獎勵

        # 用於記錄狀態比如是否已經受到在重置前只能受到一次的懲罰
        self.special_status = {}  # 特殊狀態

    def get_state(self, window_size: tuple, velocity_scale: float = 200.0, **kwargs):
        """
        獲取正規化狀態。
        使用 tanh 函數來處理沒有固定上限的速度。
        velocity_scale: 用於調整速度的靈敏度。
        """
        # 首先，從父類獲取基本狀態（位置、技能冷卻等）
        state = super().get_state(window_size=window_size, velocity_scale=velocity_scale, **kwargs)

        return state

    def reset(self, **kwargs):
        """Reset the player when dropped."""

        super().reset(**kwargs)
        self.is_alive = True
        self.is_on_ground = False
        self.special_status = {}

    def reset_episodes(self, **kwargs):
        """Reset the player at the start of each episode."""

        self.reset(**kwargs)

        self.set_last_direction(None)
        self.set_direction_count(0)

    def bot_action(self, **kwargs):
        """Generate a bot action for the player."""
        action_dict = {}
        for ability_name, ability_instance in self.abilities.items():
            action_value = ability_instance.bot_action(**kwargs)
            if action_value is not None:
                action_dict[ability_name] = action_value
        return action_dict

    def apply_force_at_world_point(self, force: pymunk.Vec2d, point: tuple[float, float]):
        self.shape.apply_force_at_world_point(force, point)

    def get_reward_per_step(self):
        return self.reward_per_step
    
    def get_last_direction(self):
        return self.last_direction

    def get_direction_count(self):
        return self.direction_count
    
    def get_special_status(self, status_key: str):
        return self.special_status.get(status_key, 0)
    
    def set_reward_per_step(self, reward: float):
        self.reward_per_step = reward
    
    def add_reward_per_step(self, reward: float):
        self.reward_per_step += reward

    def set_last_direction(self, direction: str):
        self.last_direction = direction

    def set_direction_count(self, count: int):
        self.direction_count = count

    def set_special_status(self, status_key: str, status_value):
        self.special_status[status_key] = status_value

    def add_direction_count(self, count: int):
        self.direction_count += count


