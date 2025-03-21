import pymunk
from shapes.shape import Shape
from typing import Tuple, Optional

class Circle(Shape):
    
    def __init__(
                self, 
                position: Tuple[float, float] = (300, 100), 
                velocity: Tuple[float, float] = (0, 0), 
                body: Optional[pymunk.Body] = None, 
                shape_radio: float = 20, 
                shape_mass: float = 1, 
                shape_friction: float = 0.1, 
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
        """

        super().__init__(position, velocity, body)
        self.shape_radio = shape_radio
        self.shape = pymunk.Circle(self.body, shape_radio)
        self.shape.mass = shape_mass
        self.shape.friction = shape_friction
        self.shape.elasticity = 0.8  # Add some bounce to make the simulation more interesting
