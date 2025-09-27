
import time
import pymunk
import numpy as np

from role.roles import Role
from role.shapes.shape import Shape

class Player(Role):
    def __init__(self, shape: Shape, player_color: tuple, action_params: dict, action_cooldown: dict):
        super().__init__(shape, player_color, action_params, action_cooldown)
        self.player_color = player_color
        self.action_cooldown = action_cooldown  # Dictionary of action cooldowns
        self.action_params = action_params  # Dictionary of action parameters
        self.last_action_time = {action: 0 for action in action_cooldown}  # Track last action time for each action
        self.is_alive = True
        self.is_on_ground = False

    def move(self, direction):
        force_vector = pymunk.Vec2d(direction * self.action_params["speed"], 0)
        self.shape.apply_force_at_world_point(force_vector, self.get_position())

        # # 施加角速度
        # self.shape.body.angular_velocity += p1action

    def jump(self, action):
        force_vector = pymunk.Vec2d(0, action * self.action_params["jump_high"])
        self.shape.apply_force_at_world_point(force_vector, self.get_position())

    def perform_action(self, players_action):
        # 遍歷所有玩家
        if players_action[0] != 0:
            self.move(players_action[0])

        if players_action[1] != 0 and self.is_on_ground and self.check_cooldowns("jump"):  # Jump action
            self.jump(players_action[1])
            self.last_action_time["jump"] = time.time()

        if isinstance(players_action[2], tuple) and self.check_cooldowns("collision"):  # Collision action
            # 处理旋转动作
            x, y = self.get_position()
            target_x, target_y = players_action[2]

            # 計算方向向量
            direction_vector = pymunk.Vec2d(target_x - x, target_y - y)

            # 只有在向量長度不為零時才進行計算，以避免除以零的錯誤
            if direction_vector.length > 0:
                # 正規化向量（使其長度為1）並乘以速度
                velocity_vector = direction_vector.normalized() * self.action_params["collision_speed"]
                # 直接設置速度
                self.shape.set_velocity(velocity_vector)

    def get_state(self, window_size, velocity_scale=200.0, **kwargs):
        """
        獲取玩家的正規化狀態。
        使用 tanh 函數來處理沒有固定上限的速度。
        velocity_scale: 用於調整速度的靈敏度。
        """
        # 首先，從父類獲取基本狀態（位置、技能冷卻等）
        state = super().get_state(window_size=window_size, **kwargs)

        # 接著，添加正規化的速度
        vel_x, vel_y = self.get_velocity()

        # 使用 tanh 進行正規化，velocity_scale 是一個超參數，用於調整靈敏度
        norm_vx = np.tanh(vel_x / velocity_scale)
        norm_vy = np.tanh(vel_y / velocity_scale)

        state.extend([norm_vx, norm_vy])

        return state
    
    
    def reset(self, space):
        super().reset(space)
        self.is_alive = True
        self.is_on_ground = False

    def get_is_alive(self):
        return self.is_alive

    def get_is_on_ground(self):
        return self.is_on_ground

    def set_is_alive(self, alive_status: bool):
        self.is_alive = alive_status

    def set_is_on_ground(self, on_ground: bool):
        self.is_on_ground = on_ground