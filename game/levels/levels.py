import random
import pymunk
import pygame
import numpy as np
import time

from shapes.circle import Circle

def get_level(level: int, space):
    """
    Get the level object based on the level number.
    """
    if level == 1:
        return Level1(space)
    elif level == 2:
        return Level2(space)
    elif level == 3:
        return Level3(space)
    else:
        raise ValueError("Invalid level number")

class Levels:
    def __init__(self, space, window_x: int = 1000, window_y: int = 600):
        self.space = space
        self.window_x = window_x
        self.window_y = window_y

    def create_player(self,
                      default_player_position: tuple = None,
                      ball_color = (255, 213, 79),  # Bright yellow ball
                      window_x: int = 1000,
                      window_y: int = 600,
                     ):
        """
        Create the ball with physics properties
        default_player_position: Initial position of the player
            default: (window_x / 2, window_y / 5)
        """
        if default_player_position is None:
            default_player_position = (window_x / 2, window_y / 5)
        dynamic_body = pymunk.Body()  # Ball body
        ball_radius = int(window_x / 67)
        player = Circle(
            position=default_player_position,
            velocity=(0, 0),
            body=dynamic_body,
            shape_radio=ball_radius,
            shape_friction=100,
        )
        # Store initial values for reset
        return {
            "type": "player",
            "shape": player,
            "default_position": default_player_position,
            "body": dynamic_body,
            "ball_radius": ball_radius,
            "ball_color": ball_color
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

# TODO not use for now
    def _draw_indie_style(self):
        """Draw game objects with indie game aesthetic"""
        # # Draw platform with gradient and glow
        # platform_points = []
        # for v in self.platform.get_vertices():
        #     x, y = v.rotated(self.kinematic_body.angle) + self.kinematic_body.position
        #     platform_points.append((int(x), int(y)))

        # pygame.draw.polygon(self.screen, self.PLATFORM_COLOR, platform_points)
        # pygame.draw.polygon(self.screen, (255, 255, 255), platform_points, 2)

        platform_pos = (int(self.kinematic_body.position[0]), int(self.kinematic_body.position[1]))
        pygame.draw.circle(self.screen, self.PLATFORM_COLOR, platform_pos, self.platform_length)
        pygame.draw.circle(self.screen, (255, 255, 255), platform_pos, self.platform_length, 2)

        # Draw rotation direction indicator
        self._draw_rotation_indicator(platform_pos, self.platform_length, self.kinematic_body.angular_velocity)

        # Draw ball with gradient and glow
        ball_pos = (int(self.dynamic_body.position[0]), int(self.dynamic_body.position[1]))
        pygame.draw.circle(self.screen, self.BALL_COLOR, ball_pos, self.ball_radius)
        pygame.draw.circle(self.screen, (255, 255, 255), ball_pos, self.ball_radius, 2)

# TODO not use for now
    def _draw_rotation_indicator(self, position, radius, angular_velocity):
        """Draw an indicator showing the platform's rotation direction and speed"""
        # Only draw the indicator if there's some rotation
        if abs(angular_velocity) < 0.1:
            return

        # Calculate indicator properties based on angular velocity
        indicator_color = (50, 255, 150) if angular_velocity > 0 else (255, 150, 50)
        num_arrows = min(3, max(1, int(abs(angular_velocity))))
        indicator_radius = radius - 20  # Place indicator inside the platform

        # Draw arrow indicators along the platform's circumference
        start_angle = self.kinematic_body.angle

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
            pygame.draw.line(self.screen, indicator_color, (base_x, base_y), (tip_x, tip_y), 3)

            # Draw arrowhead
            arrowhead_size = 7
            pygame.draw.circle(self.screen, indicator_color, (tip_x, tip_y), arrowhead_size)

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

        return (player, ), (platform, )

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

class Level2(Levels):
    """
    Level 1: Basic setup with a dynamic body and a static kinematic body.
    """
    def __init__(self, space):
        super().__init__(space)
        self.space = space
        self.last_angular_velocity_change_time = time.time()
        self.angular_velocity_change_timeout = 5 # sec


    def setup(self, window_x, window_y):
        player = super().create_player(window_x=window_x, window_y=window_y)
        platform = super().create_platform(window_x=window_x, window_y=window_y)
        self.space.add(player["body"], player["shape"].shape)
        self.space.add(platform["body"], platform["shape"])
        self.dynamic_body = player["body"]
        self.kinematic_body = platform["body"]
        self.default_player_position = player["default_position"]

        return (player, ), (platform, )

    def action(self):
        """
        shape state changes in the game
        """

        if time.time() - self.last_angular_velocity_change_time > self.angular_velocity_change_timeout:
            self.kinematic_body.angular_velocity = random.randrange(-1, 2, 2)
            self.last_angular_velocity_change_time = time.time()

    def reset(self):
        """
        Reset the level to its initial state.
        """
        self.dynamic_body.position = self.default_player_position
        self.dynamic_body.angular_velocity = 0
        self.dynamic_body.velocity = (0, 0)
        self.kinematic_body.angular_velocity = random.randrange(-1, 2, 2)
        self.last_angular_velocity_change_time = time.time()

        self.space.reindex_shapes_for_body(self.dynamic_body)
        self.space.reindex_shapes_for_body(self.kinematic_body)

# Two players
# NOTE: 連續動作空間和對抗式訓練
class Level3(Levels):
    """
    Level 1: Basic setup with a dynamic body and a static kinematic body.
    """
    def __init__(self, space):
        super().__init__(space)
        self.space = space


    def setup(self, window_x, window_y):
        x = window_x / 5
        player1 = super().create_player(window_x=window_x, 
                                        window_y=window_y, 
                                        default_player_position=(x*2, window_y / 5)
                                       )
        player2 = super().create_player(window_x=window_x, 
                                        window_y=window_y, 
                                        ball_color=(194, 238, 84), 
                                        default_player_position=(x*3, window_y / 5)
                                       )
        platform = super().create_platform(window_x=window_x, window_y=window_y)
        self.space.add(player1["body"], player1["shape"].shape)
        self.space.add(player2["body"], player2["shape"].shape)
        self.space.add(platform["body"], platform["shape"])
        self.dynamic_body1 = player1["body"]
        self.dynamic_body2 = player2["body"]
        self.kinematic_body = platform["body"]
        self.default_player_position1 = player1["default_position"]
        self.default_player_position2 = player2["default_position"]

        return (player1, player2), (platform, )

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
        self.dynamic_body1.position = self.default_player_position1
        self.dynamic_body1.angular_velocity = 0
        self.dynamic_body1.velocity = (0, 0)
        self.dynamic_body2.position = self.default_player_position2
        self.dynamic_body2.angular_velocity = 0
        self.dynamic_body2.velocity = (0, 0)
        self.kinematic_body.angular_velocity = random.randrange(-1, 2, 2)
        self.last_angular_velocity_change_time = time.time()

        self.space.reindex_shapes_for_body(self.dynamic_body1)
        self.space.reindex_shapes_for_body(self.dynamic_body2)
        self.space.reindex_shapes_for_body(self.kinematic_body)