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

    def _draw(self, screen, color, obj_pos=None):
        if obj_pos == None:
            x, y = self.body.position
            obj_pos = (int(x), int(y))
        pygame.draw.circle(screen, color, obj_pos, self.shape_size)
        pygame.draw.circle(screen, (255, 255, 255), obj_pos, self.shape_size, 2)
        if self.is_draw_rotation_indicator == True:
            self._draw_rotation_indicator(screen, obj_pos, self.shape_size, self.body.angular_velocity, self.body)

    def reset(self):
        super().reset()

    def get_reward_width(self):
        return self.shape_size - 5

    def _draw_rotation_indicator(self, screen, position, radius, angular_velocity, body):
        """Draw an indicator showing the platform's rotation direction and speed"""
        # Only draw the indicator if there's some rotation
        if abs(angular_velocity) < 0.1:
            return

        # Calculate indicator properties based on angular velocity
        indicator_color = (50, 255, 150) if angular_velocity > 0 else (255, 150, 50)
        num_arrows = min(3, max(1, int(abs(angular_velocity))))
        indicator_radius = radius - 20  # Place indicator inside the platform

        # Draw arrow indicators along the platform's circumference
        start_angle = body.angle

        for i in range(num_arrows):
            # Calculate arrow position
            arrow_angle = start_angle + i * (2 * np.pi / num_arrows)

            # Calculate arrow start and end points
            base_x = position[0] + int(np.cos(arrow_angle) * indicator_radius)
            base_y = position[1] + int(np.sin(arrow_angle) * indicator_radius)

            # Determine arrow direction based on angular velocity
            if angular_velocity > 0:  # Clockwise
                arrow_end_angle = arrow_angle + 0.3
            else:  # Counter-clockwise
                arrow_end_angle = arrow_angle - 0.3

            tip_x = position[0] + int(np.cos(arrow_end_angle) * (indicator_radius + 15))
            tip_y = position[1] + int(np.sin(arrow_end_angle) * (indicator_radius + 15))

            # Draw arrow line
            pygame.draw.line(screen, indicator_color, (base_x, base_y), (tip_x, tip_y), 3)

            # Draw arrowhead
            arrowhead_size = 7
            pygame.draw.circle(screen, indicator_color, (tip_x, tip_y), arrowhead_size)



