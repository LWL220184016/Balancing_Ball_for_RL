import random
import time
import pymunk

try:
    from role.player import PlayerFactory
    from role.platform import PlatformFactory
    from role.falling_rock import FallingRockFactory
    from role.falling_rock import FallingRock
except ImportError:
    from game.role.player import PlayerFactory
    from game.role.platform import PlatformFactory
    from game.role.falling_rock import FallingRockFactory
    from game.role.falling_rock import FallingRock

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from game.collision_handle import CollisionHandler
    
class Levels:
    def __init__(self, 
                 space: pymunk.Space, 
                 collision_handler: 'CollisionHandler' = None, 
                 collision_type: dict = None, 
                 player_configs: list = None, 
                 platform_configs: list = None
                ):
        self.space = space
        self.collision_handler = collision_handler
        self.collision_type = collision_type
        self.player_configs = player_configs
        self.platform_configs = platform_configs
        self.players = []
        self.platforms = []

    def setup(self, 
              window_x: int, 
              window_y: int
             ):
        """
        通用設置方法，用於創建和註冊遊戲對象。
        """
        self.collision_type_player = self.collision_type.get("player")
        self.collision_type_platform = self.collision_type.get("platform")

        player_factory = PlayerFactory(self.collision_type_player)
        platform_factory = PlatformFactory(self.collision_type_platform)

        if not self.collision_type_player or not self.collision_type_platform:
            raise ValueError(f"Invalid collision_type: {self.collision_type}, must contain 'player' and 'platform' keys with integer values")
        self.players = [player_factory.create_player(window_x, window_y, **config) for config in self.player_configs]
        self.platforms = [platform_factory.create_platform(window_x, window_y, **config) for config in self.platform_configs]


        print(f"Created {len(self.players)} players and {len(self.platforms)} platforms.")

        for player in self.players:
            body, shape = player.get_physics_components()
            self.space.add(body, shape)

        for platform in self.platforms:
            body, shape = platform.get_physics_components()
            self.space.add(body, shape)

        return self.players, self.platforms

    def action(self):
        """
        shape state changes in the game
        """
        # Noting to do in base level
        pass

    def reward(self, ball_x: float = None):
        return 0

    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """
        raise NotImplementedError(f"This method '{self.status_reset_step.__name__}' should be overridden by subclasses.")

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
    def __init__(self, 
                 space: pymunk.Space, 
                 collision_handler: 'CollisionHandler' = None, 
                 collision_type: dict = None, 
                 player_configs: list = None, 
                 platform_configs: list = None,
                 level_config: dict = None
                ):
        super().__init__(space, collision_handler, collision_type, player_configs, platform_configs)
        self.level_type = "Horizontal_viewing_angle"


        if len(platform_configs) > 1:
            raise ValueError("Level 1 only supports one platform configuration.")


    def setup(self, 
              window_x: int, 
              window_y: int, 
              reward_ball_centered: float = 0.2
             ):
        players, platforms = super().setup(window_x, window_y)
        # Set initial random velocity after setup
        platform = platforms[0]
        platform.set_angular_velocity(random.randrange(-1, 2, 2))

        self.platform_center_x = platform.get_position()[0]
        # Reward parameters
        self.reward_ball_centered = reward_ball_centered
        self.reward_width = platform.get_reward_width()

        return players, platforms, []

    def action(self):
        """
        shape state changes in the game
        """
        # Noting to do in this level
        pass

    def reward(self, ball_x: float):
        center_reward = 0

        distance_from_center = abs(ball_x - self.platform_center_x)
        if distance_from_center < self.reward_width:
            normalized_distance = distance_from_center / self.reward_width
            center_reward = self.reward_ball_centered * (1.0 - normalized_distance)

        return center_reward

    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """
        pass

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
    def __init__(self, 
                 space: pymunk.Space, 
                 collision_handler: 'CollisionHandler' = None, 
                 collision_type: dict = None, 
                 player_configs: list = None, 
                 platform_configs: list = None,
                 level_config: dict = None
                ):
        super().__init__(space, collision_handler, collision_type, player_configs, platform_configs)
        self.level_type = "Horizontal_viewing_angle"
        self.last_angular_velocity_change_time = time.time()
        self.angular_velocity_change_timeout = 5 # sec

        if len(platform_configs) > 1:
            raise ValueError("Level 2 only supports one platform configuration.")

    def setup(self, 
              window_x: int, 
              window_y: int, 
              reward_ball_centered: float = 0.2
             ):
        players, platforms = super().setup(window_x, window_y)
        # Set initial random velocity after setup
        platform = platforms[0]
        platform.set_angular_velocity(random.randrange(-1, 2, 2))

        self.platform_center_x = platform.get_position()[0]
        # Reward parameters
        self.reward_ball_centered = reward_ball_centered
        self.reward_width = platform.get_reward_width()

        return players, platforms, []

    def action(self):
        """
        shape state changes in the game
        """
        if time.time() - self.last_angular_velocity_change_time > self.angular_velocity_change_timeout:
            self.platforms[0].set_angular_velocity(random.randrange(-1, 2, 2))
            self.last_angular_velocity_change_time = time.time()

    def reward(self, ball_x: float):
        center_reward = 0

        distance_from_center = abs(ball_x - self.platform_center_x)
        if distance_from_center < self.reward_width:
            normalized_distance = distance_from_center / self.reward_width
            center_reward = self.reward_ball_centered * (1.0 - normalized_distance)

        return center_reward

    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """
        pass

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()
        for platform in self.platforms:
            platform.set_angular_velocity(random.randrange(-1, 2, 2))
        self.last_angular_velocity_change_time = time.time()

class Level3(Levels):
    """
    Level 3: Basic setup with a dynamic body and a static kinematic body.

    Two players are introduced, each with their own dynamic body.
    """
    def __init__(self, 
                 space: pymunk.Space, 
                 collision_handler: 'CollisionHandler' = None, 
                 collision_type: dict = None, 
                 player_configs: list = None, 
                 platform_configs: list = None,
                 level_config: dict = None
                ):
        super().__init__(space, collision_handler, collision_type, player_configs, platform_configs)
        self.level_type = "Horizontal_viewing_angle"
        self.collision_type = collision_type
        self.level_config = level_config
        self.falling_rocks: list[FallingRock] = []
        self.window_size = None

    def setup(self, 
              window_x: int, 
              window_y: int
             ):
        players, platforms = super().setup(window_x, window_y)
        self.window_size = (window_x, window_y)

        falling_rock_configs = self.level_config.get("falling_rock_configs")
        entities_configs = self.level_config.get("entities_configs")

        falling_rock_factory = FallingRockFactory(self.collision_type.get("fallingRock"))

        # 根據 entity_configs 的配置來創建對應數量的 falling rocks
        quantities = entities_configs.get("quantity")
        for config in falling_rock_configs:
            for _ in range(quantities.get("fallingRock")):
                rock = falling_rock_factory.create_fallingRock(window_x, window_y, **config)
                self.falling_rocks.append(rock)
                body, shape = rock.get_physics_components()
                self.space.add(body, shape)

        return players, platforms, [self.falling_rocks]

    def action(self):
        """
        shape state changes in the game
        """
        for rock in self.falling_rocks:
            pos_x, pos_y = rock.get_position()
            if pos_y > self.window_size[1] or rock.get_is_on_ground(): # 檢查是否掉出視窗底部或者落在平臺上
                rock.reset(self.space, self.window_size)

    def reward(self, ball_x: float = None):
        return 0

    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """
        for player in self.players:
            player.set_is_on_ground(False)

        for rock in self.falling_rocks:
            rock.set_is_on_ground(False)

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()
        for rock in self.falling_rocks:
            rock.reset(self.space, self.window_size)

