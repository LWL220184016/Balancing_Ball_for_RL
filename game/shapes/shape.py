import pymunk
from typing import Tuple, Optional

class Shape:

    def __init__(
                self,
                position: Tuple[float, float] = (300, 100),
                velocity: Tuple[float, float] = (0, 0),
                body: Optional[pymunk.Body] = None,
                shape: Optional[pymunk.Shape] = None,
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

        self.shape = shape

    def reset(self):
        """Reset the body to its default position, velocity and angular velocity."""
        self.body.position = self.default_position
        self.body.velocity = self.default_velocity
        self.body.angular_velocity = self.default_angular_velocity
