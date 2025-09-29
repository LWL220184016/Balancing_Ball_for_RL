import pymunk
import random

from typing import Tuple, Optional

class Shape:

    def __init__(
                self,
                position: Tuple[float, float] = (300, 100),
                velocity: Tuple[float, float] = (0, 0),
                body: Optional[pymunk.Body] = None,
            ):
        """
        Initialize a physical shape with associated body.

        Args:
            position: Initial position (x, y) of the body
            velocity: Initial velocity (vx, vy) of the body
            body: The pymunk Body to attach to this shape
            shape: The pymunk Shape for collision detection
        """

        self.body = body
        self.default_position = position
        self.default_velocity = velocity
        self.body.position = position
        self.body.velocity = velocity
        self.default_angular_velocity = 0

    def reset(self):
        """Reset the body to its default position, velocity and angular velocity."""
        
        self.body.position = self.default_position
        self.body.velocity = self.default_velocity
        self.body.angular_velocity = self.default_angular_velocity

    def apply_force_at_world_point(self, force, point):
        self.body.apply_force_at_world_point(force, point)

    def calculate_position(window_x: int, window_y: int, position: tuple):
        # if len(position) != 0:
        #     default_position = (window_x * position[0], window_y * position[1])
        # else:
        #     default_position = (random.randint(0, window_x), random.randint(0, window_y))
        # return default_position

        return (
            window_x * position[0] if isinstance(position[0], float) else random.randint(0, window_x), 
            window_y * position[1] if isinstance(position[1], float) else random.randint(0, window_y)
        )


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

    def set_default_position(self, position: Tuple[float, float]):
        self.default_position = position

    def get_velocity(self):
        return self.body.velocity[0], self.body.velocity[1]
    
    def get_angular_velocity(self):
        return self.body.angular_velocity   

    def get_physics_components(self):
        """
        Returns the physics body and shape for adding to the space.
        self.shape is defined in the subclass.
        """
        
        return self.body, self.shape
    
    def set_velocity(self, velocity: pymunk.Vec2d):
        self.body.velocity = velocity

    def set_angular_velocity(self, angle: float):
        self.body.angular_velocity = angle