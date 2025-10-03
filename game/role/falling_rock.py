import numpy as np
import pymunk
import random

try:
    from role.roles import Role
    from role.shapes.circle import Circle
    from role.shapes.rectangle import Rectangle
except ImportError:
    from game.role.roles import Role
    from game.role.shapes.circle import Circle
    from game.role.shapes.rectangle import Rectangle

class FallingRock(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        vel_x, vel_y = self.get_velocity()

        # 使用 tanh 進行正規化，velocity_scale 是一個超參數，用於調整靈敏度
        norm_vx = np.tanh(vel_x / velocity_scale)
        norm_vy = np.tanh(vel_y / velocity_scale)

        state.extend([norm_vx, norm_vy])

        return state

    def reset(self):

        super().reset()

class FallingRockFactory:
    def __init__(self, collision_type_fallingRock: int):
        self.collision_type_fallingRock = collision_type_fallingRock

    def create_fallingRock(self,
                           window_x: int = 1000,
                           window_y: int = 600,
                           space: pymunk.Space = None,
                           shape_type: str = "circle",
                           size: tuple = None,
                           shape_mass: float = None,
                           shape_friction: float = None,
                           shape_elasticity: float = None,
                           default_position: tuple = None,
                           default_velocity: tuple = None,
                           abilities: dict = None,
                           health: int | str = None,
                           color: tuple = None
                          ) -> FallingRock:
        """Create the Falling Rock with physics properties.

        Args:
            window_x (int): Width of the game window.
            window_y (int): Height of the game window.
            shape_type (str): Type of the shape, e.g., "circle", "rectangle".
            size (tuple): 
                - If shape is Circle: It is a tuple (float,) and will be the radius of the ball as a proportion of window_x.
                - If shape is Rectangle: It is a tuple (float, float, ...) and will be side lengths as a proportion of window_x and window_y.
            shape_mass (float): Mass of the Falling Rock.
            shape_friction (float): Friction of the Falling Rock.
            shape_elasticity (float): Elasticity of the Falling Rock.
            default_position (tuple(float, float)): Proportion of window_x and window_y.
            default_velocity (tuple(float, float)): Initial velocity of the Falling Rock.
            abilities (dict{str, str, ...}): Abilities of the Falling Rock.
            health (int | str): Initial health of the Falling Rock. Will be infinite health if it is a string.
            color (tuple(int, int, int)): Color of the Falling Rock.

        Returns:
            Falling Rock: The created Falling Rock object.
        """
        
        dynamic_body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)  # Falling Rock body
        
        if shape_type == "circle":
            length = int(window_x * size[0])
            shape = Circle(
                shape_size=length,
                shape_mass=shape_mass,
                shape_friction=shape_friction,
                shape_elasticity=shape_elasticity,
                body=dynamic_body,
                collision_type=self.collision_type_fallingRock,
                is_draw_rotation_indicator=True,

                # **kwargs
                window_x=window_x,
                window_y=window_y,
                default_position=default_position,
                default_velocity=default_velocity
            )


        elif shape_type == "rectangle":
            length = (size[0] * window_x, size[1] * window_y)
            shape = Rectangle(
                shape_size=length,
                shape_mass=shape_mass,
                shape_friction=shape_friction,
                shape_elasticity=shape_elasticity,
                body=dynamic_body,
                collision_type=self.collision_type_fallingRock,

                # **kwargs
                window_x=window_x,
                window_y=window_y,
                default_position=default_position,
                default_velocity=default_velocity
            )

        falling_rock = FallingRock(

            # **kwargs
            shape=shape,
            space=space,
            color=color,
            abilities=abilities,
            health=health
        )
        self.collision_type_fallingRock += 1

        return falling_rock