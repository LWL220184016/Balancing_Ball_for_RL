import pygame
import pymunk
import numpy as np

from typing import Tuple, Optional

try:
    from shapes.shape import Shape
except ImportError:
    # from role.shapes.shape import Shape
    from script.role.shapes.shape import Shape

class Circle(Shape): 

    def __init__(
                self,
                shape_size: int = None,
                shape_mass: float = None,
                shape_friction: float = None,
                shape_elasticity: float = None,
                body: Optional[pymunk.Body] = None,
                collision_type: Optional[int] = None,
                is_draw_rotation_indicator: bool = None,
                is_load_by_game_class: bool = True,
                **kwargs
            ):
        """
        Initialize a circular physics object.

        Args:
            shape_size: Diameter of the circle in pixels
            shape_mass: Mass of the circle
            shape_friction: Friction coefficient for the circle
            shape_elasticity: Elasticity (bounciness) of the circle
            body: The pymunk Body to attach this circle to
            is_load_by_game_class: If this class is loaded by the BalancingBallGame, then pymunk will need self.shape for physics simulation.
        """

        self.shape_size = shape_size / 2  # radius
        if is_load_by_game_class:
            super().__init__(body=body, **kwargs)
            self.shape = pymunk.Circle(self.body, self.shape_size)
            self.shape.mass = shape_mass
            self.shape.friction = shape_friction
            self.shape.elasticity = shape_elasticity
            self.shape.collision_type = collision_type
        self.is_draw_rotation_indicator = is_draw_rotation_indicator

    def get_draw_data(self):
        x, y = self.body.position
        obj_pos = (int(x), int(y))
        return obj_pos

    def reset(self):
        super().reset()

    def get_reward_width(self):
        return self.shape_size - 5
