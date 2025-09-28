
import pymunk
import numpy as np

from role.roles import Role
from role.shapes.shape import Shape

class Player(Role):
    def __init__(self, shape: Shape, player_color: tuple, abilities: list = [str]):
        super().__init__(shape, player_color, abilities)
        self.player_color = player_color
        self.is_alive = True
        self.is_on_ground = False

    def perform_action(self, players_action: list):
        # 遍歷所有玩家
        if players_action[0] != 0:
            self.abilities["Move"].action(players_action[0], self)

        if players_action[1] != 0:  # Jump action
            self.abilities["Jump"].action(players_action[1], self)

        if isinstance(players_action[2], tuple):  # Collision action
            # 处理旋转动作
            self.abilities["Collision"].action(players_action[2], self)

    def get_state(self, window_size: tuple, velocity_scale: float = 200.0):
        """
        獲取玩家的正規化狀態。
        使用 tanh 函數來處理沒有固定上限的速度。
        velocity_scale: 用於調整速度的靈敏度。
        """
        # 首先，從父類獲取基本狀態（位置、技能冷卻等）
        state = super().get_state(window_size=window_size)

        # 接著，添加正規化的速度
        vel_x, vel_y = self.get_velocity()

        # 使用 tanh 進行正規化，velocity_scale 是一個超參數，用於調整靈敏度
        norm_vx = np.tanh(vel_x / velocity_scale)
        norm_vy = np.tanh(vel_y / velocity_scale)

        state.extend([norm_vx, norm_vy])

        return state
    
    
    def reset(self, space: pymunk.Space):
        super().reset(space)
        self.is_alive = True
        self.is_on_ground = False

    def apply_force_at_world_point(self, force: pymunk.Vec2d, point: tuple[float, float]):
        self.shape.apply_force_at_world_point(force, point)

    def get_is_alive(self):
        return self.is_alive

    def get_is_on_ground(self):
        return self.is_on_ground

    def set_is_alive(self, alive_status: bool):
        self.is_alive = alive_status

    def set_is_on_ground(self, on_ground: bool):
        self.is_on_ground = on_ground

    def set_velocity(self, velocity: pymunk.Vec2d):
        self.shape.set_velocity(velocity)