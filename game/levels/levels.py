import random
import time
import pymunk
import numpy as np

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

    def _get_observation_state_base(self) -> np.ndarray:
        """
        Return the current observation without taking a step
        """

        pass

    def reset(self):
        """
        Reset the level to its initial state.
        """
        for player in self.players:
            player.reset_episodes()

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

        from levels.rewards.failling_rock_reward import PlayerFallingRockCollisionReward, PlayerFallingRockNearReward
        from levels.rewards.player_reward import PlayerFallAndSurvivalReward, PlayerMovementDirectionPenalty

        reward_calculator = RewardCalculator(
            players=self.players,
            platforms=None, # useless in this level
            entities=self.falling_rocks,
            collision_handler=self.collision_handler,
            reward_components_terminates=[
                PlayerFallingRockCollisionReward(self.level_configs.get("reward"))
            ],
            reward_components=[
                PlayerFallAndSurvivalReward(self.level_configs.get("reward")),
                PlayerFallingRockNearReward(self.level_configs.get("reward")),
                PlayerMovementDirectionPenalty(self.level_configs.get("reward")),
            ],
            window_x=window_x,
            window_y=window_y,
        )

        if len(self.players) != 1 or len(self.falling_rocks) != 1:
            print(f"\n\033[38;5;196mLevel 3 only supports 1 player and 1 falling rock in RL.196m\033[0m")

        return players, platforms, [self.falling_rocks], reward_calculator

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
        for player in self.players:
            player.set_is_on_ground(False)
            player.set_collision_with([])

        for rock in self.falling_rocks:
            rock.set_is_on_ground(False)

    def _get_observation_state_base(self) -> np.ndarray:
        """
        Return the current observation without taking a step.
        This version uses relative positions and velocities for better learning.
        """
        
        # Assuming one player and one rock for this level
        player = self.players[0]
        rock = self.falling_rocks[0]

        # Get normalized states for both
        player_state = player.get_state(window_size=self.window_size, velocity_scale=200.0)
        rock_state = rock.get_state(window_size=self.window_size, velocity_scale=20.0)

        # player_state = [player_norm_x, player_norm_y, player_norm_vx, player_norm_vy]
        # rock_state   = [rock_norm_x,   rock_norm_y,   rock_norm_vx,   rock_norm_vy]

        # Calculate relative position and velocity
        relative_pos_x = rock_state[0] - player_state[0]
        relative_pos_y = rock_state[1] - player_state[1]
        relative_vel_x = rock_state[2] - player_state[2]
        relative_vel_y = rock_state[3] - player_state[3]

        # The observation is the player's own velocity and the relative info to the target.
        # This tells the agent "here is your current momentum" and "here is where the target is relative to you".
        obs = [
            player_state[2],  # player_norm_vx
            player_state[3],  # player_norm_vy
            relative_pos_x,
            relative_pos_y,
            relative_vel_x,
            relative_vel_y,
            # You can also include the absolute position of the player if boundary awareness is important
            player_state[0], # player_norm_x
            player_state[1], # player_norm_y
        ]

        return np.array(obs, dtype=np.float32)

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()
        for rock in self.falling_rocks:
            rock.reset()

