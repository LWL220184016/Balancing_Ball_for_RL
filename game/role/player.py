
import pymunk
import numpy as np

try:
    from role.roles import Role
    from role.shapes.shape import Shape
    from role.shapes.circle import Circle
except ImportError:
    from game.role.roles import Role
    from game.role.shapes.shape import Shape
    from game.role.shapes.circle import Circle

class Player(Role):
    def __init__(self, shape: Shape, color: tuple, abilities: list = [str]):
        super().__init__(shape, color, abilities)
        self.color = color
        self.is_alive = True
        self.is_on_ground = False

    def perform_action(self, action: list):
        # 遍歷所有玩家
        if action[0] != 0:
            self.abilities["Move"].action(action[0], self)

        if action[1] != 0:  # Jump action
            self.abilities["Jump"].action(action[1], self)

        if isinstance(action[2], tuple):  # Collision action
            # 处理旋转动作
            self.abilities["Collision"].action(action[2], self)

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

class PlayerFactory:
    def __init__(self, collision_type_player: int):
        self.collision_type_player = collision_type_player

    def create_player(self,
                      window_x: int = 1000,
                      window_y: int = 600,
                      default_player_position: tuple = None,
                      color = None,
                      abilities: dict = None
                     ) -> Player:
        """
        Create the ball with physics properties
        default_player_position: Initial position of the player
        """

        dynamic_body = pymunk.Body()  # Ball body
        default_player_position = (window_x * default_player_position[0], window_y * default_player_position[1])
        ball_radius = int(window_x / 67)
        shape = Circle(
            position=default_player_position,
            velocity=(0, 0),
            body=dynamic_body,
            shape_size=ball_radius,
            shape_friction=100,
            collision_type=self.collision_type_player,
            draw_rotation_indicator=False
        )

        player = Player(
            shape=shape,
            color=color,
            abilities=abilities
        )
        self.collision_type_player += 1
        # Store initial values for reset
        return player