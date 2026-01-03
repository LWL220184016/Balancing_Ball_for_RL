import numpy as np

from script.game_config import GameConfig

try:
    from levels.rewards.reward_calculator import RewardCalculator
    from levels.rewards.player_reward import PlayerShotHitReward, PlayerSpeedReward, PlayerFaceToTargetReward
    from levels.levels import Levels
except ImportError:
    from script.levels.rewards.reward_calculator import RewardCalculator
    from script.levels.rewards.player_reward import PlayerShotHitReward, PlayerSpeedReward, PlayerFaceToTargetReward
    from script.levels.levels import Levels

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    pass

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

        # 測試直綫向正下方跑能達到的最大速度為 2009.5642653447935，但是考慮到對角綫跑能有更長的加速距離，因此設大了一點
        self.velocity_scale = 2100

    def setup(self):

        players, platforms = super().setup()
        self.window_size = (GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # 用於狀態空間的歸一化
        self.max_dist = np.sqrt(self.window_size[0]**2 + self.window_size[1]**2)

        for platform in platforms:
            platform.set_is_alive(False) # 設置 is_alive 成 False 能讓他們不被渲染，本來都是在地圖外面的，不渲染提升性能

        reward_calculator = RewardCalculator(
            game=self.game,
            players=self.players,
            platforms=None, # useless in this level
            entities=None,
            reward_components_terminates=[
                PlayerShotHitReward(self.level_configs.get("reward")),
            ],
            reward_components=[
                PlayerSpeedReward(self.level_configs.get("reward")),
                PlayerFaceToTargetReward(self.level_configs.get("reward")),
                # 站著不動懲罰
                # 不開槍懲罰
                # 躲避子彈獎勵
            ],
        )

        if len(self.players) != 2:
            print(f"\n\033[38;5;196mLevel 4 only supports 2 players in RL.196m\033[0m")

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
        
        obs = {}
        for p in self.players:
            self_body = p.shape.body
            self_body_rotation_vector = self_body.rotation_vector
            self_obs_cos = self_body_rotation_vector.x
            self_obs_sin = self_body_rotation_vector.y
            self_body_angle = self_body.angle
            norm_health = p.health / p.default_health

            self_pos = self_body.position
            self_vel = self_body.velocity
            norm_vx = np.tanh(self_vel[0] / self.velocity_scale)
            norm_vy = np.tanh(self_vel[1] / self.velocity_scale)

            is_player_ability_available = (self.game.steps - p.abilities["Shoot"].last_used_step) / p.abilities["Shoot"].cooldown

            for _p in self.players:
                if _p.role_id == p.role_id:
                    continue

                enemy_body = _p.shape.body
                _relative_pos = enemy_body.position - self_pos
                _relative_vel = enemy_body.velocity - self_vel
                
                relative_pos = _relative_pos.rotated(-self_body_angle)
                relative_vel = _relative_vel.rotated(-self_body_angle)

                
                norm_relative_px = relative_pos[0] / self.max_dist
                norm_relative_py = relative_pos[1] / self.max_dist
                norm_relative_vx = np.tanh(relative_vel[0] / self.velocity_scale)
                norm_relative_vy = np.tanh(relative_vel[1] / self.velocity_scale)

                # The observation is the player's own velocity and the relative info to the target.
                _obs = [
                    self_obs_cos,
                    self_obs_sin,
                    norm_health,
                    norm_vx, 
                    norm_vy, 
                    is_player_ability_available,

                    norm_relative_px,
                    norm_relative_py,
                    norm_relative_vx,
                    norm_relative_vy,
                ]

                obs[p.role_id] = np.array(_obs, dtype=np.float32)

        return obs

    def reset(self):
        """
        Reset the level to its initial state.
        """
        super().reset()