import pygame
import pymunk

from typing import Tuple, Optional

try:
    from shapes.shape import Shape
except ImportError:
    from role.shapes.shape import Shape

class Rectangle(Shape):

    def __init__(
                self,
                position: Tuple[float, float] = (300, 100),
                velocity: Tuple[float, float] = (0, 0),
                body: Optional[pymunk.Body] = None,
                shape_size: Tuple[float, float] = None,
                shape_mass: float = 1,
                shape_friction: float = 0.7,
                shape_elasticity: float = 0.1,
                collision_type: Optional[int] = None,
            ):
        """
        Initialize a rectangular physics object.

        Args:
            position: Initial position (x, y) of the rectangle
            velocity: Initial velocity (vx, vy) of the rectangle
            body: The pymunk Body to attach this rectangle to
            shape_size: Width and Height of the rectangle in pixels
            shape_mass: Mass of the rectangle
            shape_friction: Friction coefficient for the rectangle
            shape_elasticity: Elasticity (bounciness) of the rectangle
        """

        super().__init__(position, velocity, body)
        self.shape_size = shape_size
        self.shape = pymunk.Poly.create_box(self.body, shape_size)
        self.shape.mass = shape_mass
        self.shape.friction = shape_friction
        self.shape.elasticity = shape_elasticity
        self.shape.collision_type = collision_type

    def _draw(self, screen, rect_color):
        x, y = self.body.position
        rect = pygame.Rect(int(x - self.shape_size[0] / 2), int(y - self.shape_size[1] / 2), self.shape_size[0], self.shape_size[1])
        pygame.draw.rect(screen, rect_color, rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)

    def get_reward_width(self):
        return self.shape_size[0] / 2 - 5