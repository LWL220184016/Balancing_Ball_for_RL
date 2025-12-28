import pymunk

from script.game_config import GameConfig
from role.shapes.circle import Circle
from role.shapes.rectangle import Rectangle

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from role.roles import Role

class RoleFactory:
    def __init__(self, collision_type_role: int):
        self.collision_type_role = collision_type_role

    def create_role(self,
                    role_id: str = None,
                    is_alive: bool = None,
                    body: pymunk.Body = None,
                    cls: 'Role' = None,
                    space: pymunk.Space = None,
                    shape_type: str = None,
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
                   ) -> 'Role':
        """Create the role with physics properties.

        Args:
            shape_type (str): Type of the shape, e.g., "circle", "rectangle".
            size (tuple): 
                - If shape is Circle: It is a tuple (float,) and will be the radius of the ball as a proportion of window_x.
                - If shape is Rectangle: It is a tuple (float, float, ...) and will be side lengths as a proportion of window_x and window_y.
            shape_mass (float): Mass of the role.
            shape_friction (float): Friction of the role.
            shape_elasticity (float): Elasticity of the role.
            default_position (tuple(float, float)): Proportion of window_x and window_y.
            default_velocity (tuple(float, float)): Initial velocity of the role.
            abilities (dict{str, str, ...}): Abilities of the role.
            health (int | str): Initial health of the role. Will be infinite health if it is a string.
            color (tuple(int, int, int)): Color of the role.

        Returns:
            role: The created role object.
        """
        # Create game bodies
        if shape_type == "circle":
            length = int(GameConfig.scale_x(size[0]))
            shape = Circle(
                shape_size=length,
                shape_mass=shape_mass,
                shape_friction=shape_friction,
                shape_elasticity=shape_elasticity,
                body=pymunk.Body(body_type=body),
                collision_type=self.collision_type_role,
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
                body=pymunk.Body(body_type=body),
                collision_type=self.collision_type_role,

                # **kwargs
                default_position=default_position,
                default_velocity=default_velocity,
                default_angular_velocity=default_angular_velocity,
            )

        role = cls(

            # **kwargs
            role_id=role_id,
            is_alive=is_alive,
            shape=shape,
            space=space,
            color=color,
            abilities=abilities,
            health=health,
            expired_time=expired_time,
        )

        return role
    
