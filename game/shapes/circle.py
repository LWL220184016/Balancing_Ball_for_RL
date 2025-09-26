import pygame
import pymunk

from typing import Tuple, Optional

try:
    from shapes.shape import Shape
except ImportError:
    from game.shapes.shape import Shape

class Circle(Shape):

    def __init__(
                self,
                position: Tuple[float, float] = (300, 100),
                velocity: Tuple[float, float] = (0, 0),
                body: Optional[pymunk.Body] = None,
                shape_radio: float = 20,
                shape_mass: float = 1,
                shape_friction: float = 0.1,
                shape_elasticity: float = 0.8
            ):
        """
        Initialize a circular physics object.

        Args:
            position: Initial position (x, y) of the circle
            velocity: Initial velocity (vx, vy) of the circle
            body: The pymunk Body to attach this circle to
            shape_radio: Radius of the circle in pixels
            shape_mass: Mass of the circle
            shape_friction: Friction coefficient for the circle
            shape_elasticity: Elasticity (bounciness) of the circle
        """

        super().__init__(position, velocity, body, shape_mass, shape_friction, shape_elasticity)
        self.shape_radio = shape_radio
        self.shape = pymunk.Circle(self.body, shape_radio)

    def _draw(self, screen, ball_color):
        x, y = self.body.position
        radius = self.shape_radio
        ball_pos = (int(x), int(y))
        pygame.draw.circle(screen, ball_color, ball_pos, radius)
        pygame.draw.circle(screen, (255, 255, 255), ball_pos, radius, 2)