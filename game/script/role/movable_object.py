import pymunk

from script.game_config import GameConfig

try:
    from role.roles import Role
    from role.shapes.circle import Circle
    from role.shapes.rectangle import Rectangle
except ImportError:
    from script.role.roles import Role
    from script.role.shapes.circle import Circle
    from script.role.shapes.rectangle import Rectangle

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

class MovableObjectFactory:
    def __init__(self, collision_type_movableObject: int):
        self.collision_type_movableObject = collision_type_movableObject

    def create_movableObject(self,
                             role_id: str = None,
                             space: pymunk.Space = None,
                             shape_type: str = "circle",
                             size: tuple = None,
                             shape_mass: float = None,
                             shape_friction: float = None,
                             shape_elasticity: float = None,
                             default_position: tuple = None,
                             default_velocity: tuple = None,
                             default_angular_velocity: float = None,
                             abilities: dict = None,
                             health: int | str = None,
                             color: tuple = None,
                             expired_time: int = None,
                            ) -> MovableObject:
        """Create the Movable Object with physics properties.

        Args:
            shape_type (str): Type of the shape, e.g., "circle", "rectangle".
            size (tuple): 
                - If shape is Circle: It is a tuple (float,) and will be the radius of the ball as a proportion of window_x.
                - If shape is Rectangle: It is a tuple (float, float, ...) and will be side lengths as a proportion of window_x and window_y.
            shape_mass (float): Mass of the Movable Object.
            shape_friction (float): Friction of the Movable Object.
            shape_elasticity (float): Elasticity of the Movable Object.
            default_position (tuple(float, float)): Proportion of window_x and window_y.
            default_velocity (tuple(float, float)): Initial velocity of the Movable Object.
            abilities (dict{str, str, ...}): Abilities of the Movable Object.
            health (int | str): Initial health of the Movable Object. Will be infinite health if it is a string.
            color (tuple(int, int, int)): Color of the Movable Object.

        Returns:
            Movable Object: The created Movable Object object.
        """

        dynamic_body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)  # Movable Object body

        if shape_type == "circle":
            length = int(GameConfig.scale_x(size[0]))
            shape = Circle(
                shape_size=length,
                shape_mass=shape_mass,
                shape_friction=shape_friction,
                shape_elasticity=shape_elasticity,
                body=dynamic_body,
                collision_type=self.collision_type_movableObject,
                is_draw_rotation_indicator=True,

                # **kwargs
                default_position=default_position,
                default_velocity=default_velocity,
                default_angular_velocity=default_angular_velocity,
            )


        elif shape_type == "rectangle":
            length = (GameConfig.scale_x(size[0]), GameConfig.scale_y(size[1]))
            shape = Rectangle(
                shape_size=length,
                shape_mass=shape_mass,
                shape_friction=shape_friction,
                shape_elasticity=shape_elasticity,
                body=dynamic_body,
                collision_type=self.collision_type_movableObject,

                # **kwargs
                default_position=default_position,
                default_velocity=default_velocity,
                default_angular_velocity=default_angular_velocity,
            )

        movable_object = MovableObject(
            # **kwargs
            role_id=role_id,
            shape=shape,
            space=space,
            color=color,
            abilities=abilities,
            health=health,
            expired_time=expired_time,
        )
        self.collision_type_movableObject += 1

        return movable_object