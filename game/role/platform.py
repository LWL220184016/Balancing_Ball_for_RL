
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
    def __init__(self, shape: Shape, color: tuple, abilities: list[str]):
        super().__init__(shape, color, abilities)
        self.color = color

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
                        platform_shape_type: str = None,
                        platform_proportion: float = None,
                        platform_position: tuple = None,
                        color = None,
                        abilities: dict = None
                       ) -> Platform:
        """
        Create the platform with physics properties
        platform_shape_type: circle, rectangle
        platform_length: Length of a rectangle or Diameter of a circle
        """
        # Create game bodies
        kinematic_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)  # Platform body
        kinematic_body.position = (window_x * platform_position[0], window_y * platform_position[1])
        default_kinematic_position = kinematic_body.position
        platform_length = int(window_x * platform_proportion)

        if platform_shape_type == "circle":
            platform_length = platform_length / 2 # radius
            shape = Circle(
                position=default_kinematic_position,
                velocity=(0, 0),
                body=kinematic_body,
                shape_size=platform_length,
                shape_friction=0.7,
                collision_type=self.collision_type_platform,
                draw_rotation_indicator=True,
            )


        elif platform_shape_type == "rectangle":
            platform_length = platform_length
            shape = Rectangle(
                position=default_kinematic_position,
                velocity=(0, 0),
                body=kinematic_body,
                shape_size=(platform_length, 20),
                shape_friction=0.7,
                shape_elasticity=0.1,
                collision_type=self.collision_type_platform,
            )

        platform = Platform(
            shape, 
            color,
            abilities=abilities
        )

        return platform