import random
import time
import pymunk

try:
    from role.player import PlayerFactory
    from role.platform import PlatformFactory
    from role.falling_rock import FallingRockFactory
    from role.falling_rock import FallingRock
    from levels.rewards.reward_calculator import RewardCalculator
except ImportError:
    from game.role.player import PlayerFactory
    from game.role.platform import PlatformFactory
    from game.role.falling_rock import FallingRockFactory
    from game.role.falling_rock import FallingRock
    from game.levels.rewards.reward_calculator import RewardCalculator

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from game.collision_handle import CollisionHandler
    from role.player import Player
    from role.platform import Platform
    
class Levels:
    def __init__(self, 
                 space: pymunk.Space, 
                 collision_handler: 'CollisionHandler' = None, 
                 collision_type: dict = None, 
                 player_configs: list = None, 
                 level_configs: list = None
                ):
        self.space = space
        self.collision_handler = collision_handler
        self.collision_type = collision_type
        self.player_configs = player_configs
        self.level_configs = level_configs
        self.players = []
        self.platforms = []

    def setup(self, 
              window_x: int, 
              window_y: int
             ):
        """
        通用設置方法，用於創建和註冊遊戲對象。
        """
        self.collision_type_player: int = self.collision_type.get("player")
        self.collision_type_platform: int = self.collision_type.get("platform")

        player_factory = PlayerFactory(self.collision_type_player)
        platform_factory = PlatformFactory(self.collision_type_platform)

        if not self.collision_type_player or not self.collision_type_platform:
            raise ValueError(f"Invalid collision_type: {self.collision_type}, must contain 'player' and 'platform' keys with integer values")
        self.players: list['Player'] = [player_factory.create_player(window_x=window_x, window_y=window_y, space=self.space, **config) for config in self.player_configs]
        self.platforms: list['Platform'] = [platform_factory.create_platform(window_x=window_x, window_y=window_y, space=self.space, **config) for config in self.level_configs.get("platform_configs")]

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

    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """

        pass

    def reset(self):
        """
        Reset the level to its initial state.
        """
        for player in self.players:
            player.reset()

        for platform in self.platforms:
            platform.reset()


class Level1(Levels):
    """
    Level 1: Basic setup with a dynamic body and a static kinematic body.
    """
    def __init__(self, 
                 **kwargs
                ):
        super().__init__(**kwargs)
        self.level_type = "Horizontal_viewing_angle"


        if len(self.level_configs.get("platform_configs", [])) > 1:
            raise ValueError("Level 1 only supports one platform configuration.")


    def setup(self, 
              window_x: int, 
              window_y: int, 
             ):
        players, platforms = super().setup(window_x, window_y)
        # Set initial random velocity after setup
        platform = platforms[0]
        platform.set_angular_velocity(random.randrange(-1, 2, 2))

        from levels.rewards.player_reward import PlayerFallAndSurvivalReward, PlayerStayInPlatformCenterReward

        reward_calculator = RewardCalculator(
            players=self.players, 
            platforms=platforms,
            entities=None, # useless in this level
            collision_handler=self.collision_handler,
            reward_components_terminates=[
                PlayerFallAndSurvivalReward(self.level_configs.get("reward"))
            ],
            reward_components=[
                PlayerStayInPlatformCenterReward(self.level_configs.get("reward"))
            ], 
            window_x=window_x,
            window_y=window_y,
        )

        return players, platforms, [], reward_calculator

    def action(self):
        """
        shape state changes in the game
        """
        # Noting to do in this level
        pass

    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """
        
        super().status_reset_step()

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
                 **kwargs
                ):
        super().__init__(**kwargs)
        self.level_type = "Horizontal_viewing_angle"
        self.last_angular_velocity_change_time = time.time()
        self.angular_velocity_change_timeout = 5 # sec

        if len(self.level_configs.get("platform_configs", [])) > 1:
            raise ValueError("Level 2 only supports one platform configuration.")

    def setup(self, 
              window_x: int, 
              window_y: int, 
             ):
        players, platforms = super().setup(window_x, window_y)
        # Set initial random velocity after setup
        platform = platforms[0]
        platform.set_angular_velocity(random.randrange(-1, 2, 2))

        from levels.rewards.player_reward import PlayerFallAndSurvivalReward, PlayerStayInPlatformCenterReward

        reward_calculator = RewardCalculator(
            players=self.players, 
            platforms=platforms, 
            entities=None, # useless in this level
            collision_handler=self.collision_handler, 
            reward_components_terminates=[
                PlayerFallAndSurvivalReward(self.level_configs.get("reward"))
            ],
            reward_components=[
                PlayerStayInPlatformCenterReward(self.level_configs.get("reward"))
            ], 
            window_x=window_x, 
            window_y=window_y, 
        )

        return players, platforms, [], reward_calculator

    def action(self):
        """
        shape state changes in the game
        """
        if time.time() - self.last_angular_velocity_change_time > self.angular_velocity_change_timeout:
            self.platforms[0].set_angular_velocity(random.randrange(-1, 2, 2))
            self.last_angular_velocity_change_time = time.time()

    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """

        super().status_reset_step()

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
                 **kwargs
                ):
        super().__init__(**kwargs)
        self.level_type = "Horizontal_viewing_angle"
        self.falling_rocks: list[FallingRock] = []
        self.window_size = None

    def setup(self, 
              window_x: int, 
              window_y: int
             ):

        players, platforms = super().setup(window_x, window_y)
        self.window_size = (window_x, window_y)

        falling_rock_configs = self.level_configs.get("falling_rock_configs")
        entities_configs = self.level_configs.get("entities_configs")

        falling_rock_factory = FallingRockFactory(self.collision_type.get("fallingRock"))

        # 根據 entity_configs 的配置來創建對應數量的 falling rocks
        quantities = entities_configs.get("quantity")
        for config in falling_rock_configs:
            for _ in range(quantities.get("fallingRock")):
                rock = falling_rock_factory.create_fallingRock(window_x=window_x, window_y=window_y, space=self.space, **config)
                self.falling_rocks.append(rock)
                body, shape = rock.get_physics_components()
                self.space.add(body, shape)

        from levels.rewards.failling_rock_reward import PlayerFallingRockCollisionReward
        from levels.rewards.player_reward import PlayerFallAndSurvivalReward

        reward_calculator = RewardCalculator(
            players=self.players,
            platforms=None, # useless in this level
            entities=self.falling_rocks,
            collision_handler=self.collision_handler,
            reward_components_terminates=[
                PlayerFallingRockCollisionReward(self.level_configs.get("reward"))
            ],
            reward_components=[
                PlayerFallAndSurvivalReward(self.level_configs.get("reward"))
            ],
            window_x=window_x,
            window_y=window_y,
        )

        return players, platforms, [self.falling_rocks], reward_calculator

    def action(self):
        """
        shape state changes in the game
        """

        # Noting to do in this level
        pass
    
    # reward parameters defined in class Level self.__init__
    def reward(self):
        
        for rock in self.falling_rocks:
            penalty = 0
            if rock.get_is_on_ground():
                penalty = self.falling_rock_fall_on_platform
                rock.reset()
                continue  # 如果石頭已經落地，跳過這次檢查

            pos_x, pos_y = rock.get_position()
            if pos_x < 0 or pos_x > self.window_size[0] or pos_y > self.window_size[1]: # 檢查是否掉出視窗底部或者落在平臺上
                collision_type = rock.get_last_collision_with()
                player = self.collision_handler.get_player_from_collision_type(collision_type)
                if player:
                    player.add_reward_per_step(self.falling_rock_fall_outside_platform)
                rock.reset()

        for player in self.players:
            if not player.get_is_alive():
                continue
            
            player.add_reward_per_step(penalty)
            collision_list = player.get_collision_with()
            for collision in collision_list:
                if self.collision_handler.check_is_entities(collision): # 假設 falling_rock 屬於 entities
                    player.add_reward_per_step(self.collision_falling_rock)

        
            

    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """
        
        super().status_reset_step()
        for player in self.players:
            player.set_is_on_ground(False)
            player.set_collision_with([])

        for rock in self.falling_rocks:
            rock.set_is_on_ground(False)

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()
        for rock in self.falling_rocks:
            rock.reset()

