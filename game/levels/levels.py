import random
import pymunk
from shapes.circle import Circle

def get_level(level: int, space):
    """
    Get the level object based on the level number.
    """
    if level == 1:
        return Level1(space)
    # elif level == 2:
        # return Level2(space)
    # elif level == 3:
        # return Level3()
    else:
        raise ValueError("Invalid level number")

class Levels:
    def __init__(self, space, window_x: int = 1000, window_y: int = 600):
        self.space = space
        self.window_x = window_x
        self.window_y = window_y

    def create_player(self,
                      window_x: int = 1000,
                      window_y: int = 600,
                     ):
        """Create the ball with physics properties"""
        dynamic_body = pymunk.Body()  # Ball body
        ball_radius = int(window_x / 67)
        player = Circle(
            position=(window_x / 2, window_y / 5),
            velocity=(0, 0),
            body=dynamic_body,
            shape_radio=ball_radius,
            shape_friction=100,
        )
        # Store initial values for reset
        default_player_position = (window_x / 2, window_y / 5)
        return {
            "type": "player",
            "shape": player,
            "default_position": default_player_position,
            "body": dynamic_body,
            "ball_radius": ball_radius,
        }

    def create_platform(self,
                        platform_shape: str = "circle",
                        platform_proportion: float = 0.4,
                        window_x: int = 1000,
                        window_y: int = 600,
                       ):
        """
        Create the platform with physics properties
        platform_shape: circle, rectangle
        platform_length: Length of a rectangle or Diameter of a circle
        """
        platform_length = int(window_x * platform_proportion)

        # Create game bodies
        kinematic_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)  # Platform body
        kinematic_body.position = (window_x / 2, (window_y / 3) * 2)
        default_kinematic_position = kinematic_body.position

        if platform_shape == "circle":
            platform_length = platform_length / 2 # radius
            platform = pymunk.Circle(kinematic_body, platform_length)
            platform.mass = 1  # 质量对 Kinematic 物体无意义，但需要避免除以零错误
            platform.friction = 0.7

        elif platform_shape == "rectangle":
            platform_length = platform_length
            vs = [(-platform_length/2, -10),
                (platform_length/2, -10),
                (platform_length/2, 10),
                (-platform_length/2, 10)]

            platform = pymunk.Poly(kinematic_body, vs)
        platform.friction = 0.7
        platform.rotation = 0
        kinematic_body.angular_velocity = random.randrange(-1, 2, 2)

        return {
            "type": "platform",
            "shape": platform,
            "default_position": default_kinematic_position,
            "body": kinematic_body,
            "platform_length": platform_length,
        }

class Level1(Levels):
    """
    Level 1: Basic setup with a dynamic body and a static kinematic body.
    """
    def __init__(self, space):
        super().__init__(space)
        self.space = space


    def setup(self, window_x, window_y):
        player = super().create_player(window_x=window_x, window_y=window_y)
        platform = super().create_platform(window_x=window_x, window_y=window_y)
        self.space.add(player["body"], player["shape"].shape)
        self.space.add(platform["body"], platform["shape"])
        self.dynamic_body = player["body"]
        self.kinematic_body = platform["body"]
        self.default_player_position = player["default_position"]

        return (player), (platform)

    def action(self):
        """
        shape state changes in the game
        """
        # Noting to do in this level
        pass

    def reset(self):
        """
        Reset the level to its initial state.
        """
        self.dynamic_body.position = self.default_player_position
        self.dynamic_body.angular_velocity = 0
        self.dynamic_body.velocity = (0, 0)
        self.kinematic_body.angular_velocity = random.randrange(-1, 2, 2)

        self.space.reindex_shapes_for_body(self.dynamic_body)
        self.space.reindex_shapes_for_body(self.kinematic_body)
