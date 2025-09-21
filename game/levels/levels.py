import random
import pymunk
import pygame
import numpy as np
import time
import json
import os

try:
    from shapes.circle import Circle
except ImportError:
    from game.shapes.circle import Circle

def get_level(level: int, space, player_configs=None, platform_configs=None):
    """
    Get the level object based on the level number.
    """
    if not player_configs or not platform_configs:
        # Get the directory of the current script
        print("Loading default level configurations...")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(dir_path, './level_default_cfg.json')
        with open(config_path, 'r') as f:
            default_configs = json.load(f)
        
        level_key = f"level{level}"
        if level_key in default_configs:
            level_cfg = default_configs[level_key]
            if not player_configs:
                player_configs = level_cfg.get("player_configs", [])
            if not platform_configs:
                platform_configs = level_cfg.get("platform_configs", [])
        else:
            raise ValueError(f"Default config for level {level} not found in {config_path}")

    if not player_configs:
        raise ValueError(f"Invalid player_configs: {player_configs}, must be a non-empty list or dict")

    if not platform_configs:
        raise ValueError(f"Invalid platform_configs: {platform_configs}, must be a non-empty list or dict")

    print(f"Using player_configs: {player_configs}")
    print(f"Using platform_configs: {platform_configs}")
    if level == 1:
        return Level1(space, player_configs, platform_configs)
    elif level == 2:
        return Level2(space, player_configs, platform_configs)
    elif level == 3:
        return Level3(space, player_configs, platform_configs)
    else:
        raise ValueError(f"Invalid level number: {level}")

class Levels:
    def __init__(self, space, player_configs=None, platform_configs=None):
        self.space = space
        self.player_configs = player_configs
        self.platform_configs = platform_configs
        self.players = []
        self.platforms = []

    def setup(self, window_x, window_y):
        """
        通用設置方法，用於創建和註冊遊戲對象。
        """
        self.players = [self.create_player(window_x, window_y, **config) for config in self.player_configs]
        self.platforms = [self.create_platform(window_x, window_y, **config) for config in self.platform_configs]

        print(f"Created {len(self.players)} players and {len(self.platforms)} platforms.")

        for player in self.players:
            self.space.add(player["body"], player["shape"].shape)
        
        for platform in self.platforms:
            self.space.add(platform["body"], platform["shape"])

        return tuple(self.players), tuple(self.platforms)

    def create_player(self,
                      window_x: int = 1000,
                      window_y: int = 600,
                      default_player_position: tuple = None,
                      ball_color = None,  
                     ):
        """
        Create the ball with physics properties
        default_player_position: Initial position of the player
        """
        default_player_position = (window_x * default_player_position[0], window_y * default_player_position[1])
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
                        window_x: int = 1000,
                        window_y: int = 600,
                        platform_shape_type: str = None,
                        platform_proportion: float = None,
                        platform_position: tuple = None,
                       ):
        """
        Create the platform with physics properties
        platform_shape_type: circle, rectangle
        platform_length: Length of a rectangle or Diameter of a circle
        """
        platform_length = int(window_x * platform_proportion)

        # Create game bodies
        kinematic_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)  # Platform body
        kinematic_body.position = (window_x * platform_position[0], window_y * platform_position[1])
        default_kinematic_position = kinematic_body.position

        if platform_shape_type == "circle":
            platform_length = platform_length / 2 # radius
            platform = pymunk.Circle(kinematic_body, platform_length)
            platform.mass = 1  # 质量对 Kinematic 物体无意义，但需要避免除以零错误
            platform.friction = 0.7

        elif platform_shape_type == "rectangle":
            platform_length = platform_length
            vs = [(-platform_length/2, -10),
                (platform_length/2, -10),
                (platform_length/2, 10),
                (-platform_length/2, 10)]

            platform = pymunk.Poly(kinematic_body, vs)
        platform.friction = 0.7
        platform.rotation = 0

        return {
            "type": "platform",
            "platform_shape_type": platform_shape_type,
            "shape": platform,
            "default_position": default_kinematic_position,
            "body": kinematic_body,
            "platform_length": platform_length,
        }

    def reset(self):
        """
        Reset the level to its initial state.
        """
        for player in self.players:
            player_body = player["body"]
            player_body.position = player["default_position"]
            player_body.angular_velocity = 0
            player_body.velocity = (0, 0)
            self.space.reindex_shapes_for_body(player_body)

        for platform in self.platforms:
            platform_body = platform["body"]
            platform_body.position = platform["default_position"]
            platform_body.angular_velocity = 0
            platform_body.velocity = (0, 0)
            self.space.reindex_shapes_for_body(platform_body)

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
    def __init__(self, space, player_configs=None, platform_configs=None):
        super().__init__(space, player_configs, platform_configs)
        self.space = space
        self.player_ball_speed = 5000
        self.player_configs = player_configs

    def setup(self, window_x, window_y):
        players, platforms = super().setup(window_x, window_y)
        # Set initial random velocity after setup
        for platform in platforms:
            platform["body"].angular_velocity = random.randrange(-1, 2, 2)
        return players, platforms

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
        super().reset()
        
        for platform in self.platforms:
            platform["body"].angular_velocity = random.randrange(-1, 2, 2)

class Level2(Levels):
    """
    Level 2: Basic setup with a dynamic body and a static kinematic body.
    
    The kinematic body changes its angular velocity every few seconds.
    """
    def __init__(self, space, player_configs=None, platform_configs=None):
        super().__init__(space, player_configs, platform_configs)
        self.space = space
        self.player_ball_speed = 5000
        self.player_configs = player_configs
        self.last_angular_velocity_change_time = time.time()
        self.angular_velocity_change_timeout = 5 # sec

    def setup(self, window_x, window_y):
        players, platforms = super().setup(window_x, window_y)
        # Set initial random velocity after setup
        for platform in platforms:
            platform["body"].angular_velocity = random.randrange(-1, 2, 2)

        return players, platforms

    def action(self):
        """
        shape state changes in the game
        """
        platform_body = self.platforms[0]["body"]
        if time.time() - self.last_angular_velocity_change_time > self.angular_velocity_change_timeout:
            platform_body.angular_velocity = random.randrange(-1, 2, 2)
            self.last_angular_velocity_change_time = time.time()

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()
        for platform in self.platforms:
            platform["body"].angular_velocity = random.randrange(-1, 2, 2)
        self.last_angular_velocity_change_time = time.time()

# Two players
# NOTE: 連續動作空間和對抗式訓練
class Level3(Levels):
    """
    Level 3: Basic setup with a dynamic body and a static kinematic body.

    Two players are introduced, each with their own dynamic body.
    """
    def __init__(self, space, player_configs=None, platform_configs=None):
        super().__init__(space, player_configs, platform_configs)
        self.space = space
        self.player_ball_speed = 5000
        self.player_configs = player_configs
        self.last_collision_time = 0
        self.collision_reward_cooldown = 0.5  # seconds
        self.collision_occurred = False
        self.collision_impulse_1 = 0
        self.collision_impulse_2 = 0

    def setup(self, window_x, window_y):
        players, platforms = super().setup(window_x, window_y)

        # Set collision types for balls - 這是關鍵修復
        players[0]["shape"].shape.collision_type = 1
        players[1]["shape"].shape.collision_type = 2

        # # Add collision handler for balls colliding with each other
        # handler = self.space.add_collision_handler(1, 2)
        # handler.begin = self.handle_collision
        
        self.collision_occurred = False

        return players, platforms

    def handle_collision(self, arbiter, space, data):
        """Handle collisions between balls"""
        current_time = time.time()
        if current_time - self.last_collision_time > self.collision_reward_cooldown:
            self.last_collision_time = current_time
            # Mark that a collision occurred
            self.collision_occurred = True
            
            # 計算碰撞時的相對速度來決定獎勵
            body1, body2 = arbiter.shapes[0].body, arbiter.shapes[1].body
            
            # 計算碰撞前的動量
            self.collision_impulse_1 = abs(body1.velocity[0]) + abs(body1.velocity[1])
            self.collision_impulse_2 = abs(body2.velocity[0]) + abs(body2.velocity[1])
            
            print(f"Collision occurred! Body1 speed: {self.collision_impulse_1:.2f}, Body2 speed: {self.collision_impulse_2:.2f}")
        return True

    def action(self):
        """
        shape state changes in the game
        """
        # Reset collision flag each frame in step function, not here
        pass

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()
        player1_body = self.players[0]["body"]
        player2_body = self.players[1]["body"]
        platform_body = self.platforms[0]["body"]

        player1_body.position = self.players[0]["default_position"]
        player1_body.angular_velocity = 0
        player1_body.velocity = (0, 0)
        
        player2_body.position = self.players[1]["default_position"]
        player2_body.angular_velocity = 0
        player2_body.velocity = (0, 0)

        self.collision_occurred = False
        self.last_collision_time = 0
        self.collision_impulse_1 = 0
        self.collision_impulse_2 = 0

        self.space.reindex_shapes_for_body(player1_body)
        self.space.reindex_shapes_for_body(player2_body)
        self.space.reindex_shapes_for_body(platform_body)