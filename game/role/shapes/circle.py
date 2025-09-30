import pygame
import pymunk
import numpy as np

from typing import Tuple, Optional

try:
    from shapes.shape import Shape
except ImportError:
    from role.shapes.shape import Shape

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
        """

        super().__init__(body=body, **kwargs)
        self.shape_size = shape_size / 2  # radius
        self.shape = pymunk.Circle(self.body, self.shape_size)
        self.shape.mass = shape_mass
        self.shape.friction = shape_friction
        self.shape.elasticity = shape_elasticity
        self.shape.collision_type = collision_type
        self.is_draw_rotation_indicator = is_draw_rotation_indicator

    def _draw(self, screen, color):
        x, y = self.body.position
        ball_pos = (int(x), int(y))
        pygame.draw.circle(screen, color, ball_pos, self.shape_size)
        pygame.draw.circle(screen, (255, 255, 255), ball_pos, self.shape_size, 2)
        if self.is_draw_rotation_indicator == True:
            self._draw_rotation_indicator(screen, ball_pos, self.shape_size, self.body.angular_velocity, self.body)

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

    def get_reward_width(self):
        return self.shape_size - 5
    
    def reset(self):
        super().reset()