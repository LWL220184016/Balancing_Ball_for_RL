import random
import pymunk
import pygame
import numpy as np
import time
import json
import os


try:
    from role.shapes.circle import Circle
    from role.shapes.rectangle import Rectangle
    from role.player import Player
    from role.platform import Platform
except ImportError:
    from game.role.shapes.circle import Circle
    from game.role.shapes.rectangle import Rectangle
    from game.role.player import Player
    from game.role.platform import Platform

def get_level(level: int, space, collision_type=None, player_configs=None, platform_configs=None, environment_configs=None):
    """
    Get the level object based on the level number.
    """
    if not player_configs or not platform_configs or not environment_configs:
        # Get the directory of the current script
        print("Loading default level configurations...")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(dir_path, './level_default_cfg.json')
        with open(config_path, 'r') as f:
            default_configs = json.load(f)
        
        level_key = f"level{level}"
        if level_key in default_configs:
            level_cfg = default_configs[level_key]
            if not collision_type:
                collision_type = level_cfg.get("collision_type", {})
            if not player_configs:
                player_configs = level_cfg.get("player_configs", [])
            if not platform_configs:
                platform_configs = level_cfg.get("platform_configs", [])
            if not environment_configs:
                environment_configs = level_cfg.get("environment_configs", [])
        else:
            raise ValueError(f"Default config for level {level} not found in {config_path}")

    if not player_configs:
        raise ValueError(f"Invalid player_configs: {player_configs}, must be a non-empty list or dict")

    if not environment_configs:
        raise ValueError(f"Invalid environment_configs: {environment_configs}, must be a non-empty list or dict")

    print(f"Using collision_type: {collision_type}")
    print(f"Using player_configs: {player_configs}")
    print(f"Using platform_configs: {platform_configs}")
    print(f"Using environment_configs: {environment_configs}")

    space.gravity = tuple(environment_configs[0].get("gravity"))
    space.damping = environment_configs[0].get("damping")

    if level == 1:
        return Level1(space, collision_type, player_configs, platform_configs)
    elif level == 2:
        return Level2(space, collision_type, player_configs, platform_configs)
    elif level == 3:
        return Level3(space, collision_type, player_configs, platform_configs)
    else:
        raise ValueError(f"Invalid level number: {level}")

class Levels:
    def __init__(self, space, collision_type=None, player_configs=None, platform_configs=None):
        self.space = space
        self.collision_type = collision_type
        self.player_configs = player_configs
        self.platform_configs = platform_configs
        self.players = []
        self.platforms = []

    def setup(self, window_x, window_y):
        """
        通用設置方法，用於創建和註冊遊戲對象。
        """
        self.collision_type_player = self.collision_type.get("player")
        self.collision_type_platform = self.collision_type.get("platform")
        if not self.collision_type_player or not self.collision_type_platform:
            raise ValueError(f"Invalid collision_type: {self.collision_type}, must contain 'player' and 'platform' keys with integer values")
        self.players = [self.create_player(window_x, window_y, **config) for config in self.player_configs]
        self.platforms = [self.create_platform(window_x, window_y, **config) for config in self.platform_configs]


        print(f"Created {len(self.players)} players and {len(self.platforms)} platforms.")

        for player in self.players:
            body, shape = player.get_physics_components()
            self.space.add(body, shape)

        for platform in self.platforms:
            body, shape = platform.get_physics_components()
            self.space.add(body, shape)

        return self.players, self.platforms

    def create_player(self,
                      window_x: int = 1000,
                      window_y: int = 600,
                      default_player_position: tuple = None,
                      player_color = None,
                      action_params: dict = None,
                      action_cooldown: dict = None
                     ):
        """
        Create the ball with physics properties
        default_player_position: Initial position of the player
        """
        dynamic_body = pymunk.Body()  # Ball body
        default_player_position = (window_x * default_player_position[0], window_y * default_player_position[1])
        ball_radius = int(window_x / 67)
        shape = Circle(
            position=default_player_position,
            velocity=(0, 0),
            body=dynamic_body,
            shape_size=ball_radius,
            shape_friction=100,
            collision_type=self.collision_type_player,
            draw_rotation_indicator=False
        )

        player = Player(
            shape=shape,
            player_color=player_color,
            action_params=action_params,
            action_cooldown=action_cooldown
        )
        self.collision_type_player += 1
        # Store initial values for reset
        return player

    def create_platform(self,
                        window_x: int = 1000,
                        window_y: int = 600,
                        platform_shape_type: str = None,
                        platform_proportion: float = None,
                        platform_position: tuple = None,
                        platform_color = None,
                       ):
        """
        Create the platform with physics properties
        platform_shape_type: circle, rectangle
        platform_length: Length of a rectangle or Diameter of a circle
        """
        # Create game bodies
        kinematic_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)  # Platform body
        kinematic_body.position = (window_x * platform_position[0], window_y * platform_position[1])
        default_kinematic_position = kinematic_body.position
        platform_length = int(window_x * platform_proportion)

        if platform_shape_type == "circle":
            platform_length = platform_length / 2 # radius
            shape = Circle(
                position=default_kinematic_position,
                velocity=(0, 0),
                body=kinematic_body,
                shape_size=platform_length,
                shape_friction=0.7,
                collision_type=self.collision_type_platform,
                draw_rotation_indicator=True,
            )


        elif platform_shape_type == "rectangle":
            platform_length = platform_length
            shape = Rectangle(
                position=default_kinematic_position,
                velocity=(0, 0),
                body=kinematic_body,
                shape_size=(platform_length, 20),
                shape_friction=0.7,
                shape_elasticity=0.1,
                collision_type=self.collision_type_platform,
            )

        platform = Platform(
            shape, 
            platform_color, 
            action_params={}, 
            action_cooldown={}
        )

        return platform
    
    def reset(self):
        """
        Reset the level to its initial state.
        """
        for player in self.players:
            player.reset(self.space)

        for platform in self.platforms:
            platform.reset(self.space)

class Level1(Levels):
    """
    Level 1: Basic setup with a dynamic body and a static kinematic body.
    """
    def __init__(self, space, collision_type=None, player_configs=None, platform_configs=None):
        super().__init__(space, collision_type, player_configs, platform_configs)
        self.level_type = "Horizontal_viewing_angle"
        self.space = space
        self.player_configs = player_configs

        if len(platform_configs) > 1:
            raise ValueError("Level 1 only supports one platform configuration.")


    def setup(self, window_x, window_y, reward_ball_centered=0.2):
        players, platforms = super().setup(window_x, window_y)
        # Set initial random velocity after setup
        platform = platforms[0]
        platform.set_angular_velocity(random.randrange(-1, 2, 2))

        self.platform_center_x = platform.get_position()[0]
        # Reward parameters
        self.reward_ball_centered = reward_ball_centered
        self.reward_width = platform.get_reward_width()

        return players, platforms

    def action(self):
        """
        shape state changes in the game
        """
        # Noting to do in this level
        pass

    def reward(self, ball_x):
        center_reward = 0

        distance_from_center = abs(ball_x - self.platform_center_x)
        if distance_from_center < self.reward_width:
            normalized_distance = distance_from_center / self.reward_width
            center_reward = self.reward_ball_centered * (1.0 - normalized_distance)

        return center_reward

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()
        for platform in self.platforms:
            platform.set_angular_velocity(random.randrange(-1, 2, 2))

class Level2(Levels):
    """
    Level 2: Basic setup with a dynamic body and a static kinematic body.
    
    The kinematic body changes its angular velocity every few seconds.
    """
    def __init__(self, space, collision_type=None, player_configs=None, platform_configs=None):
        super().__init__(space, collision_type, player_configs, platform_configs)
        self.level_type = "Horizontal_viewing_angle"
        self.space = space
        self.player_configs = player_configs
        self.last_angular_velocity_change_time = time.time()
        self.angular_velocity_change_timeout = 5 # sec

        if len(platform_configs) > 1:
            raise ValueError("Level 2 only supports one platform configuration.")

    def setup(self, window_x, window_y, reward_ball_centered=0.2):
        players, platforms = super().setup(window_x, window_y)
        # Set initial random velocity after setup
        platform = platforms[0]
        platform.set_angular_velocity(random.randrange(-1, 2, 2))

        self.platform_center_x = platform.get_position()[0]
        # Reward parameters
        self.reward_ball_centered = reward_ball_centered
        self.reward_width = platform.get_reward_width()

        return players, platforms

    def action(self):
        """
        shape state changes in the game
        """
        if time.time() - self.last_angular_velocity_change_time > self.angular_velocity_change_timeout:
            self.platforms[0].set_angular_velocity(random.randrange(-1, 2, 2))
            self.last_angular_velocity_change_time = time.time()

    def reward(self, ball_x):
        center_reward = 0

        distance_from_center = abs(ball_x - self.platform_center_x)
        if distance_from_center < self.reward_width:
            normalized_distance = distance_from_center / self.reward_width
            center_reward = self.reward_ball_centered * (1.0 - normalized_distance)

        return center_reward

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()
        for platform in self.platforms:
            platform.set_angular_velocity(random.randrange(-1, 2, 2))
        self.last_angular_velocity_change_time = time.time()

# Two players
# NOTE: 連續動作空間和對抗式訓練
class Level3(Levels):
    """
    Level 3: Basic setup with a dynamic body and a static kinematic body.

    Two players are introduced, each with their own dynamic body.
    """
    def __init__(self, space, collision_type=None, player_configs=None, platform_configs=None):
        super().__init__(space, collision_type, player_configs, platform_configs)
        self.level_type = "Horizontal_viewing_angle"
        self.space = space
        self.player_configs = player_configs

    def setup(self, window_x, window_y):
        players, platforms = super().setup(window_x, window_y)

        return players, platforms

    def action(self):
        """
        shape state changes in the game
        """
        pass

    def reward(self, ball_x=None):
        return 0

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()