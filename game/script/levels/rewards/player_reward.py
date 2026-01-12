import collections
import math
import pymunk
from pymunk import Vec2d

from script.game_config import GameConfig
from levels.rewards.reward_calculator import RewardComponent, terminates_round

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from script.balancing_ball_game import BalancingBallGame
    from script.role.player import Player
    from script.collision_handle import CollisionHandler

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

@terminates_round
class PlayerShotHitReward(RewardComponent):
    """處理玩家一直向同一個方向移動的懲罰"""

    def calculate(self, players: list['Player'], collision_handler: 'CollisionHandler', **kwargs):
        default_collision_type = GameConfig.COLLISION_TYPES
        rev_default_collision_type = {int(v/1000): k for k, v in default_collision_type.items()}

        for player in players:
            if not player.get_is_alive():
                continue

            current_hit_cooldown = player.get_special_status("being_hit")
            if current_hit_cooldown > 0:
                player.set_special_status("being_hit", current_hit_cooldown - 1)
                continue
            
            for ct in player.get_collision_with():
                _ct = ct - default_collision_type["player"]
                try:
                    target_key = rev_default_collision_type[int(_ct/1000)]
                except KeyError:
                    # 我設計的判斷機制是 player 的 collision_type 是 1000 開始，平臺是 2000 開始，子彈是 3000 開始，
                    # 如果會同時存在多個玩家/平臺就會在基礎上+1，子彈的 collision_type 不太一樣，創建的時候會把發動技能的玩家的 collision_type + 他自己基礎的 3000，并不會+1。
                    # 因此如果玩家數量少於平臺的時候(兩個玩家四個平臺)，就有可能出現 ct 是 1002 的結果，但是判斷的都是整的千位數，
                    # 因此出現 1002 會導致 KeyError 但實際上不用管
                    continue
                
                if target_key == "bullet":
                    player_ct = ct - default_collision_type[target_key]

                    if player_ct != player.get_collision_type():
                        shotted_player = collision_handler.get_player_from_collision_type(player_ct)
                        # print(f"玩家 {shotted_player.role_id} 使用技能射擊命中了玩家 {player.role_id}")
                        shotted_player.add_reward_per_step(self.shooting_hit_reward)
                        player.add_reward_per_step(self.being_hit_penalty)
                        player.decrease_health(1)
                        player.set_special_status("being_hit", GameConfig.FPS * 0.1)

                        if player.health == 0:
                            shotted_player.add_reward_per_step(self.round_end_reward)
                            player.set_is_alive(False)

class PlayerSurvivalReward(RewardComponent):
    """生存獎勵(step 的總獎勵乘以倍率)"""

    def calculate(self, game: 'BalancingBallGame', players: list['Player'], **kwargs):
        step = game.get_step()
        for i, player in enumerate(players):
            if not player.get_is_alive():
                continue

            else:
                # 基礎生存獎勵
                reward_per_step_multiplier = (self.reward_per_step_multiplier * step) + 1
                reward = player.get_reward_per_step() * reward_per_step_multiplier
                player.set_reward_per_step(reward)

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

    def __init__(self, configs):
        super().__init__(configs)

    def calculate(self, players: list['Player'], **kwargs):
        # 速度獎勵 - 鼓勵保持移動
        for player in players:
            if not player.get_is_alive():
                continue
            vx, vy = player.get_velocity()
            current_speed = abs(vx) + abs(vy)
            if current_speed > self.speed_reward_threshold:
                player.add_reward_per_step(current_speed * self.speed_reward_proportion)  # 限制最大速度獎勵

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

class PlayerFaceToTargetReward(RewardComponent):
    """
    玩家在一定角度內面對目標的獎勵 (Fov Reward)。
    範圍：左右 60 度 (總共 120 度)。
    特點：
    1. 只要在扇形內獎勵相同 (支持提前量，不強制瞄準中心)。
    2. 增加距離限制 (太遠瞄準沒意義)。
    3. (可選) 增加視線檢查 (Raycast)。
    """
    
    def __init__(self, configs):
        super().__init__(configs)
        # 將角度轉換爲點積閾值。
        # cos(60) = 0.5。如果夾角 < 60度，則 dot_product > 0.5
        half_angle = self.fov_degrees / 2
        self.min_dot_product = math.cos(math.radians(half_angle)) 
        self.max_dist_sq = self.max_dist ** 2  # 使用距離平方比較，避免開根號，性能更好

    def calculate(self, game: 'BalancingBallGame', players: list['Player'], **kwargs):
        space = game.space 

        for player in players:
            if not player.get_is_alive():
                continue
            
            body = player.shape.body
            player_facing = Vec2d(1, 0).rotated(body.angle)
            player_pos = body.position
            
            # 獲取自身半徑用於避開射線自檢
            my_radius = 20.0 # 默認值
            if hasattr(player, 'shape') and isinstance(player.shape, pymunk.Circle):
                my_radius = player.shape.radius

            has_valid_target = False

            for other in players:
                if other is player or not other.get_is_alive():
                    continue
                
                other_body = other.shape.body
                other_pos = other_body.position
                to_enemy = other_pos - player_pos
                
                # 優化：距離平方檢查
                dist_sq = to_enemy.get_length_sqrd()
                if dist_sq > self.max_dist_sq:
                    continue

                # 注意：這裡一定要先算 normalized，後面計算起點要用
                to_enemy_normalized = to_enemy.normalized()

                # 角度檢查
                dot_result = player_facing.dot(to_enemy_normalized)

                if dot_result >= self.min_dot_product:
                    
                    # === 修正部分開始 ===
                    # 計算射線起點：從圓心向目標方向移動 (半徑 + 安全距離)
                    # 這樣射線起點就在玩家身體外面，不會撞到自己
                    ray_start = player_pos + to_enemy_normalized * (my_radius + 5.0)
                    
                    segment_query = space.segment_query_first(
                        ray_start,  # 使用新的起點
                        other_pos, 
                        1, 
                        pymunk.ShapeFilter(mask=pymunk.ShapeFilter.ALL_MASKS())
                    )
                    # === 修正部分結束 ===

                    # 現在如果 segment_query 為 None，說明中間無障礙物（直接通透）
                    # 或者如果撞到了東西，檢查撞到的是不是目標
                    if segment_query is None or segment_query.shape.body == other_body:
                        has_valid_target = True
                        break 

            if has_valid_target:
                angular_velocity = abs(body.angular_velocity)
                player.add_reward_per_step(self.face_to_target_reward / angular_velocity if angular_velocity > 1 else self.face_to_target_reward)
            # else:
            #     player.add_reward_per_step(-self.face_to_target_reward)

class PlayerMovementDirectionPenalty(RewardComponent):
    """處理玩家一直向同一個方向移動的懲罰"""
    action_histories = None

    def calculate(self, game: 'BalancingBallGame', players: list['Player'], **kwargs):

        if self.action_histories is None:
            # 使用列表推導式來確保每個 deque 都是獨立的物件
            self.action_histories = [
                collections.deque(maxlen=self.steps_limit_for_movement_penalty) for _ in range(len(players))
            ]

        step_actions = game.get_step_action()
        for i, player in enumerate(players):
            if not player.get_is_alive() or step_actions:
                continue
            
            history = self.action_histories[i]
            current_action = step_actions[i] # 假設 action 是一個可比較的值 (例如 1, -1, 0)

            if current_action != 0 and current_action in history and not player.get_special_status("movement_penalty"):
                player.add_reward_per_step(self.movement_penalty)
                player.set_special_status("movement_penalty", True)

            history.append(current_action)




