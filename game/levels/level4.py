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
        self.level_type = "TopDown_viewing_angle"
        self.window_size = None


    def setup(self, 
              window_x: int, 
              window_y: int
             ):

        players, platforms = super().setup(window_x, window_y)
        self.window_size = (window_x, window_y)

        reward_calculator = RewardCalculator(
            game=self.game,
            players=self.players,
            platforms=None, # useless in this level
            entities=None,
            reward_components_terminates=[
            ],
            reward_components=[
            ],
            window_x=window_x,
            window_y=window_y,
        )

        return players, platforms, [], reward_calculator

    def action(self, rewards, terminated):
        """
        shape state changes in the game
        """

        return rewards, terminated


    def status_reset_step(self):
        """
        Reset status that needs to be reset every step.
        """
        
        super().status_reset_step()
        for player in self.players:
            player.set_collision_with([])

    def _get_observation_state_based(self) -> np.ndarray:
        """
        Return the current observation without taking a step.
        This version uses relative positions and velocities for better learning.
        """
        
        # Assuming one player and one rock for this level
        player = self.players[0]

        # Get normalized states for both
        player_state = player.get_state(window_size=self.window_size, velocity_scale=200.0)

        player_pos = player_state.get("pos")
        player_vel = player_state.get("vel")

        # The observation is the player's own velocity and the relative info to the target.
        # This tells the agent "here is your current momentum" and "here is where the target is relative to you".
        obs = [
            player_vel[0], 
            player_vel[1], 
            # You can also include the absolute position of the player if boundary awareness is important
            player_pos[0], 
            player_pos[1], 
        ]

        return np.array(obs, dtype=np.float32)

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()