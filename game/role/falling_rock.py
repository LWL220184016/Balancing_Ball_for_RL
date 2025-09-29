import numpy as np
import pymunk
import random

try:
    from role.roles import Role
    from role.shapes.shape import Shape
    from role.shapes.circle import Circle
    from role.shapes.rectangle import Rectangle
except ImportError:
    from game.role.roles import Role
    from game.role.shapes.shape import Shape
    from game.role.shapes.circle import Circle
    from game.role.shapes.rectangle import Rectangle

class FallingRock(Role):
    def __init__(self, shape: Shape, color: tuple, abilities: list[str]):
        super().__init__(shape, color, abilities)
        self.color = color

    def perform_action(self, action: list):
        raise NotImplementedError(f"This method '{self.perform_action.__name__}' not implemented.")

    def get_state(self, window_size: tuple, velocity_scale: float = 20.0, **kwargs):
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

    def reset(self, space: pymunk.Space, window_size: tuple = None):
        if window_size:
            # 在 x 軸上隨機選擇一個新位置，y 軸位置保持在頂部
            new_x = random.uniform(0, window_size[0])
            new_y = self.shape.get_default_position()[1] # 保持原來的 y 高度

            self.shape.set_default_position((new_x, new_y))
        
        super().reset(space)

class FallingRockFactory:
    def __init__(self, collision_type_fallingRock: int):
        self.collision_type_fallingRock = collision_type_fallingRock

    def create_fallingRock(self,
                           window_x: int = 1000,
                           window_y: int = 600,
                           shape_type: str = "circle",
                           size: tuple = None,
                           shape_mass: float = None,
                           shape_friction: float = None,
                           shape_elasticity: float = None,
                           default_position: tuple = None,
                           default_velocity: tuple = None,
                           abilities: dict = None,
                           color: tuple = None
                          ) -> FallingRock:
        """
        Create the fallingRock with physics properties
        fallingRock_shape_type: circle, rectangle
        fallingRock_length: Length of a rectangle or Diameter of a circle
        """
        
        dynamic_body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)  # Platform body
        default_position = Shape.calculate_position(window_x, window_y, default_position)
        
        if shape_type == "circle":
            length = int(window_x * size[0])
            shape = Circle(
                shape_size=length,
                shape_mass=shape_mass,
                shape_friction=shape_friction,
                shape_elasticity=shape_elasticity,
                position=default_position,
                velocity=default_velocity,
                body=dynamic_body,
                collision_type=self.collision_type_fallingRock,
                is_draw_rotation_indicator=True
            )


        elif shape_type == "rectangle":
            length = (size[0] * window_x, size[1] * window_y)
            shape = Rectangle(
                shape_size=length,
                shape_mass=shape_mass,
                shape_friction=shape_friction,
                shape_elasticity=shape_elasticity,
                position=default_position,
                velocity=default_velocity,
                body=dynamic_body,
                collision_type=self.collision_type_fallingRock
            )

        falling_rock = FallingRock(
            shape, 
            color,
            abilities=abilities
        )

        return falling_rock