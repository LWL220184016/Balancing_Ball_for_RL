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
    from levels.levels import Levels
except ImportError:
    from game.role.player import PlayerFactory
    from game.role.platform import PlatformFactory
    from game.role.falling_rock import FallingRockFactory
    from game.role.falling_rock import FallingRock
    from game.levels.rewards.reward_calculator import RewardCalculator
    from game.levels.levels import Levels

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from game.balancing_ball_game import BalancingBallGame
    from game.collision_handle import CollisionHandler
    from role.player import Player
    from role.platform import Platform

class Level4(Levels):
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
        from levels.rewards.player_reward import PlayerFallAndSurvivalReward, PlayerMovementDirectionPenalty, PlayerSurvivalReward

        reward_calculator = RewardCalculator(
            game=self.game,
            players=self.players,
            platforms=None, # useless in this level
            entities=self.falling_rocks,
            reward_components_terminates=[
                PlayerFallingRockCollisionReward(self.level_configs.get("reward"))
            ],
            reward_components=[
                # 并非真的參予獎勵計算，只是用來檢測玩家是否掉落并且重設位置
                PlayerFallAndSurvivalReward(self.level_configs.get("reward")),

                PlayerFallingRockNearReward(self.level_configs.get("reward")),
                PlayerSurvivalReward(self.level_configs.get("reward")),
                
                PlayerMovementDirectionPenalty(self.level_configs.get("reward")),
            ],
            window_x=window_x,
            window_y=window_y,
        )

        if len(self.players) != 1 or len(self.falling_rocks) != 1:
            print(f"\n\033[38;5;196mLevel 3 only supports 1 player and 1 falling rock in RL.196m\033[0m")

        return players, platforms, [self.falling_rocks], reward_calculator

    def action(self, rewards, terminated):
        """
        shape state changes in the game
        """

        player = self.players[0]

        while not player.check_ability_ready("Collision", self.game.get_step()) and not terminated:
            self.status_reset_step()
            self.space.step(1/self.game.get_fps())

            # Check game state
            self.game.add_step(1)
            _rewards, terminated = self.game.reward()
            self.game.set_step_rewards(_rewards)
            for i, r in enumerate(_rewards):
                rewards[i] += r

            self.game.handle_pygame_events() 

        return rewards, terminated


    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """
        
        super().status_reset_step()
        for player in self.players:
            player.set_collision_with([])

        for rock in self.falling_rocks:
            rock.set_is_on_ground(False)

    def _get_observation_state_based(self) -> np.ndarray:
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

        player_pos = player_state.get("pos")
        rock_pos   = rock_state.get("pos")
        player_vel = player_state.get("vel")
        rock_vel   = rock_state.get("vel")

        # Calculate relative position and velocity
        relative_pos_x = rock_pos[0] - player_pos[0]
        relative_pos_y = rock_pos[1] - player_pos[1]
        relative_vel_x = rock_vel[0] - player_vel[0]
        relative_vel_y = rock_vel[1] - player_vel[1]

        # The observation is the player's own velocity and the relative info to the target.
        # This tells the agent "here is your current momentum" and "here is where the target is relative to you".
        obs = [
            player_vel[0], 
            player_vel[1], 
            relative_pos_x,
            relative_pos_y,
            relative_vel_x,
            relative_vel_y,
            # You can also include the absolute position of the player if boundary awareness is important
            player_pos[0], 
            player_pos[1], 
            # Add absolute position and velocity of the falling rock
            rock_pos[0],   
            rock_pos[1],   
            rock_vel[0],   
            rock_vel[1],   
        ]

        return np.array(obs, dtype=np.float32)

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()
        for rock in self.falling_rocks:
            rock.reset()

