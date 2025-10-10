from game.role import player
from levels.rewards.reward_calculator import RewardComponent, terminates_round

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.balancing_ball_game import BalancingBallGame
    from game.role.player import Player
    from game.collision_handle import CollisionHandler

@terminates_round
class PlayerFallAndSurvivalReward(RewardComponent):
    """處理墜落懲罰、基礎生存獎勵(固定值)"""

    def _is_fallen(self, player: 'Player', window_x: int, window_y: int) -> bool:
        """檢查玩家是否墜落"""
        ball_x, ball_y = player.get_position()
        return ball_y < 0 or ball_y > window_y or \
               ball_x < 0 or ball_x > window_x

    def calculate(self, players: list['Player'], window_x: int, window_y: int, **kwargs):
        for player in players:
            if not player.get_is_alive():
                continue

            if self._is_fallen(player, window_x, window_y):
                player.add_reward_per_step(self.fail_penalty)
                
                if self._terminates_round:
                    if player.decrease_health(1) and player.get_health() <= 0:
                        player.set_is_alive(False)
                        continue  # 玩家死亡，處理下一個玩家

                player.reset(health=player.get_health())
            else:
                # 基礎生存獎勵
                player.add_reward_per_step(self.reward_per_step_fixed_value)

class PlayerSurvivalReward(RewardComponent):
    """生存獎勵(step 的總獎勵乘以倍率)"""

    def calculate(self, game: 'BalancingBallGame', players: list['Player'], **kwargs):
        step = game.get_current_step()
        for i, player in enumerate(players):
            if not player.get_is_alive():
                continue

            else:
                # 基礎生存獎勵
                reward_per_step_multiplier = (self.reward_per_step_multiplier * step) + 1
                reward = player.get_reward_per_step() * reward_per_step_multiplier
                player.set_reward_per_step(reward)
                print(f"Player {i} survived for {step} steps, reward multiplier: {reward_per_step_multiplier}, total reward this step: {reward}")


class PlayerOpponentFellReward(RewardComponent):
    """處理對手掉落的獎勵"""

    def calculate(self, players: list['Player'], num_of_players_fell_this_step: int, **kwargs):
        for player in players:
            if not player.get_is_alive():
                continue
            
            if num_of_players_fell_this_step > 0:
                total_reward = self.opponent_fell_reward * num_of_players_fell_this_step
                player.add_reward_per_step(total_reward)

class PlayerSpeedReward(RewardComponent):
    """處理玩家速度獎勵"""

    def calculate(self, players: list['Player'], **kwargs):
        # 速度獎勵 - 鼓勵保持移動
        for player in players:
            if not player.get_is_alive():
                continue
            vx, vy = player.get_velocity()
            current_speed = abs(vx) + abs(vy)
            player.add_reward_per_step(min(current_speed * self.speed_reward_proportion, 0.1))  # 限制最大速度獎勵

class PlayerCollisionPlayerReward(RewardComponent):
    """處理與玩家碰撞的獎勵/懲罰"""

    def calculate(self, players: list['Player'], collision_handler: 'CollisionHandler', **kwargs):
        raise NotImplementedError("PlayerCollisionPlayerReward is currently disabled.")
        
        # reward = self.params.get("collision_player", 0.5)
        # penalty = self.params.get("collision_penalty_player", -0.5)
        # for player in players:
        #     if not player.get_is_alive():
        #         continue
            
        #     for ct in player.get_collision_with():
        #         if collision_handler.check_is_players(ct):
        #             if collision_handler.check_is_self_collision(player, ct):
        #                 player.add_reward_per_step(penalty)
        #             else:
        #                 player.add_reward_per_step(reward)

class PlayerStayInPlatformCenterReward(RewardComponent):
    """處理玩家保持在平台中心的獎勵"""

    def calculate(self, players: list['Player'], platform_center_x: int, reward_width: float, **kwargs):
        for player in players:
            center_reward = 0.0
            ball_x = player.get_position()[0]

            distance_from_center = abs(ball_x - platform_center_x)
            if distance_from_center < reward_width:
                normalized_distance = distance_from_center / reward_width
                center_reward = self.reward_ball_centered * (1.0 - normalized_distance) # TODO Hard code
            player.add_reward_per_step(center_reward)

class PlayerMovementDirectionPenalty(RewardComponent):
    """處理玩家一直向同一個方向移動的懲罰"""

    def calculate(self, players: list['Player'], **kwargs):
        for player in players:
            if not player.get_is_alive():
                continue
            
            vx, vy = player.get_velocity()
            if abs(vx) > 0.1:  # 假設0.1是速度的閾值
                if player.get_last_direction() is None:
                    player.set_last_direction('right' if vx > 0 else 'left')
                    player.set_direction_count(1)
                else:
                    current_direction = 'right' if vx > 0 else 'left'
                    if current_direction == player.get_last_direction():
                        player.add_direction_count(1)
                    else:
                        player.set_last_direction(current_direction)
                        player.set_direction_count(1)

                if player.get_direction_count() > self.steps_limit_for_movement_penalty:  # 如果連續 720 個 step 以上向同一方向移動，扣分 TODO Hard code
                    player.add_reward_per_step(self.movement_penalty)
