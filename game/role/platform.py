
import numpy as np
import pymunk

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

class Platform(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def perform_action(self, action: list):
        raise NotImplementedError(f"This method '{self.perform_action.__name__}' not implemented.")
    
    def get_reward_width(self):
        return self.shape.get_reward_width()

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
    
    def reset(self, space: pymunk.Space):
        super().reset(space)

class PlatformFactory:
    def __init__(self, collision_type_platform: int):
        self.collision_type_platform = collision_type_platform

    def create_platform(self,
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
                       ) -> Platform:
        """Create the platform with physics properties.

        Args:
            window_x (int): Width of the game window.
            window_y (int): Height of the game window.
            shape_type (str): Type of the shape, e.g., "circle", "rectangle".
            size (tuple): 
                - If shape is Circle: It is a tuple (float,) and will be the radius of the ball as a proportion of window_x.
                - If shape is Rectangle: It is a tuple (float, float, ...) and will be side lengths as a proportion of window_x and window_y.
            shape_mass (float): Mass of the platform.
            shape_friction (float): Friction of the platform.
            shape_elasticity (float): Elasticity of the platform.
            default_position (tuple(float, float)): Proportion of window_x and window_y.
            default_velocity (tuple(float, float)): Initial velocity of the platform.
            abilities (dict{str, str, ...}): Abilities of the platform.
            color (tuple(int, int, int)): Color of the platform.

        Returns:
            Platform: The created platform object.
        """
        # Create game bodies
        kinematic_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)  # Platform body

        if shape_type == "circle":
            length = int(window_x * size[0])
            shape = Circle(
                shape_size=length,
                shape_mass=shape_mass,
                shape_friction=shape_friction,
                shape_elasticity=shape_elasticity,
                body=kinematic_body,
                collision_type=self.collision_type_platform,
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
                body=kinematic_body,
                collision_type=self.collision_type_platform,

                # **kwargs
                window_x=window_x,
                window_y=window_y,
                default_position=default_position,
                default_velocity=default_velocity
            )

        platform = Platform(

            # **kwargs
            shape=shape,
            color=color,
            abilities=abilities
        )

        return platform