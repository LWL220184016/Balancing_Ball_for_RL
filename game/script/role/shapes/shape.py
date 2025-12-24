import pymunk
import random

from typing import Tuple, Optional
from script.game_config import GameConfig

class Shape:

    def __init__(
                self,
                body: pymunk.Body = None,
                default_position: Tuple[float, float] = None,
                default_velocity: Tuple[float, float] = None,
                default_angular_velocity: float = None,
            ):
        """
        Initialize a physical shape with associated body.

        Args:
            default_position: Proportion of window for initial position (x, y) of the body 
            default_velocity: Initial velocity (vx, vy) of the body
            body: The pymunk Body to attach to this shape
            shape: The pymunk Shape for collision detection
        """

        self.body = body

        self.window_x = GameConfig.SCREEN_WIDTH
        self.window_y = GameConfig.SCREEN_HEIGHT
        self.default_position = (
            self.window_x * default_position[0] if isinstance(default_position[0], float) else (self.window_x * default_position[0][0], self.window_x * default_position[0][1]),
            self.window_y * default_position[1] if isinstance(default_position[1], float) else (self.window_y * default_position[1][0], self.window_y * default_position[1][1])
        )
        self.default_velocity = default_velocity
        self.default_angular_velocity = default_angular_velocity

        if self.window_x is None or self.window_y is None or self.default_position is None or self.default_velocity is None:
            print("window_x:", self.window_x)
            print("window_y:", self.window_y)
            print("default_position:", self.default_position)
            print("default_velocity:", self.default_velocity)
            raise ValueError("window_x, window_y, default_position, and default_velocity must be provided as keyword arguments.")

        self.set_position_absolute_value(self.default_position)
        self.set_velocity(self.default_velocity)
        self.set_angular_velocity(self.default_angular_velocity)

    def reset(self):
        """Reset the body to its default position, velocity and angular velocity."""

        self.set_position_absolute_value(self.default_position)
        self.set_velocity(self.default_velocity)
        self.set_angular_velocity(self.default_angular_velocity)

    def apply_force_at_world_point(self, force, point):
        self.body.apply_force_at_world_point(force, point)

    def _draw(self, screen, color):
        raise NotImplementedError(f"This method '{self._draw.__name__}' should be implemented by subclasses.")

    def get_reward_width(self):
        raise NotImplementedError(f"This method '{self.get_reward_width.__name__}' should be implemented by subclasses.")
    
    def get_size(self):
        """
        shape_size is defined in the subclass.
        """

        return self.shape_size
    
    def get_collision_type(self):
        """
        collision_type is defined in the subclass.
        """

        return self.shape.collision_type

    def get_position(self):
        return self.body.position[0], self.body.position[1]
    
    def get_default_position(self):
        return self.default_position[0], self.default_position[1]

    def get_velocity(self):
        return self.body.velocity[0], self.body.velocity[1]
    
    def get_default_velocity(self):
        return self.default_velocity[0], self.default_velocity[1]
    
    def get_angular_velocity(self):
        return self.body.angular_velocity   

    def get_physics_components(self):
        """
        Returns the physics body and shape for adding to the space.
        self.shape is defined in the subclass.
        """
        
        return self.body, self.shape

    def set_position_absolute_value(self, position: tuple):
        """
        Set position using absolute values.
        position: (x, y) where x and y can be float (absolute value) or others (random value)
        """
        self.body.position = (
            position[0] if isinstance(position[0], float) else random.uniform(position[0][0], position[0][1]),
            position[1] if isinstance(position[1], float) else random.uniform(position[1][0], position[1][1])
        )

    def set_position_proportion(self, position: tuple):
        """
        Set position using proportion values.
        position: (x, y) where x and y are floats representing the proportion of the window size
        """
        self.body.position = (
            self.window_x * position[0] if isinstance(position[0], float) else random.uniform(self.window_x * position[0][0], self.window_x * position[0][1]),
            self.window_y * position[1] if isinstance(position[1], float) else random.uniform(self.window_y * position[1][0], self.window_y * position[1][1])
        )

    def set_default_position(self, position: Tuple[float, float]):
        self.default_position = position

    def set_velocity(self, velocity: pymunk.Vec2d):
        self.body.velocity = ( 
            velocity[0] if isinstance(velocity[0], (float, int)) else random.uniform(velocity[0][0], velocity[0][1]), 
            velocity[1] if isinstance(velocity[1], (float, int)) else random.uniform(velocity[1][0], velocity[1][1])
        )

    def set_default_velocity(self, velocity: Tuple[float, float]):
        self.default_velocity = velocity

    def set_angular_velocity(self, angle: float):
        self.body.angular_velocity = angle