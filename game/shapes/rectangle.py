import pygame
import pymunk

from typing import Tuple, Optional

try:
    from shapes.shape import Shape
except ImportError:
    from game.shapes.shape import Shape

class Rectangle(Shape):

    def __init__(
                self,
                position: Tuple[float, float] = (300, 100),
                velocity: Tuple[float, float] = (0, 0),
                body: Optional[pymunk.Body] = None,
                shape_width: float = None,
                shape_height: float = None,
                shape_mass: float = None,
                shape_friction: float = None,
                shape_elasticity: float = None
            ):
        """
        Initialize a rectangular physics object.

        Args:
            position: Initial position (x, y) of the rectangle
            velocity: Initial velocity (vx, vy) of the rectangle
            body: The pymunk Body to attach this rectangle to
            shape_width: Width of the rectangle in pixels
            shape_height: Height of the rectangle in pixels
            shape_mass: Mass of the rectangle
            shape_friction: Friction coefficient for the rectangle
            shape_elasticity: Elasticity (bounciness) of the rectangle
        """

        super().__init__(position, velocity, body, shape_mass, shape_friction, shape_elasticity)
        self.shape_width = shape_width
        self.shape_height = shape_height
        self.shape = pymunk.Poly.create_box(self.body, (shape_width, shape_height))

    def _draw(self, screen, rect_color):
        x, y = self.body.position
        rect = pygame.Rect(int(x - self.shape_width / 2), int(y - self.shape_height / 2), self.shape_width, self.shape_height)
        pygame.draw.rect(screen, rect_color, rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)