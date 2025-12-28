import pygame
import pymunk
import math

from typing import Tuple, Optional

try:
    from shapes.shape import Shape
except ImportError:
    # from role.shapes.shape import Shape
    from script.role.shapes.shape import Shape

class Rectangle(Shape):

    def __init__(
                self,
                shape_size: Tuple[float, float] = None,
                shape_mass: float = None,
                shape_friction: float = None,
                shape_elasticity: float = None,
                body: Optional[pymunk.Body] = None,
                collision_type: Optional[int] = None,
                is_load_by_game_class: bool = True,
                **kwargs
            ):
        """
        Initialize a rectangular physics object.

        Args:
            shape_size: Width and Height of the rectangle in pixels
            shape_mass: Mass of the rectangle
            shape_friction: Friction coefficient for the rectangle
            shape_elasticity: Elasticity (bounciness) of the rectangle
            body: The pymunk Body to attach this rectangle to
            is_load_by_game_class: If this class is loaded by the BalancingBallGame, then pymunk will need self.shape for physics simulation.
        """

        self.shape_size = shape_size
        if is_load_by_game_class:
            super().__init__(body=body, **kwargs)
            self.shape = pymunk.Poly.create_box(self.body, shape_size)
            self.shape.mass = shape_mass
            self.shape.friction = shape_friction
            self.shape.elasticity = shape_elasticity
            self.shape.collision_type = collision_type

    def get_draw_data(self):
        obj_pos = [self.body.local_to_world(v) for v in self.shape.get_vertices()]
        return obj_pos
    
    def reset(self):
        super().reset()

    def get_reward_width(self):
        return self.shape_size[0] / 2 - 5
    

    