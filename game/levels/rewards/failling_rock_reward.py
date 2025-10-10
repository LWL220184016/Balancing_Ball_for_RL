import pymunk
from levels.rewards.reward_calculator import RewardComponent, terminates_round

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.role.player import Player
    from game.role.falling_rock import FallingRock
    from game.collision_handle import CollisionHandler

@terminates_round
class PlayerFallingRockCollisionReward(RewardComponent):
    """處理與實體 (如落石) 的碰撞獎勵/懲罰"""
    def calculate(self, 
                  players: list['Player'], 
                  falling_rocks: list['FallingRock'], 
                  collision_handler: 'CollisionHandler', 
                  window_x: int, 
                  window_y: int,
                  **kwargs
                 ):
                  
        
        penalty = 0
        for rock in falling_rocks:
            if rock.get_is_on_ground():
                penalty = self.falling_rock_fall_on_platform
                rock.reset()
                continue  # 如果石頭已經落地，跳過這次檢查

            pos_x, pos_y = rock.get_position()
            if pos_x < 0 or pos_x > window_x or pos_y > window_y: # 檢查是否掉出視窗底部或者落在平臺上
                collision_type = rock.get_last_collision_with()
                player = collision_handler.get_player_from_collision_type(collision_type)
                if player:
                    player.add_reward_per_step(self.falling_rock_fall_outside_platform)
                rock.reset()

        for player in players:
            if not player.get_is_alive():
                continue
            
            player.add_reward_per_step(penalty)
            if penalty < 0:
                
                if self._terminates_round:
                    if player.decrease_health(1) and player.get_health() <= 0:
                        player.set_is_alive(False)
                        continue  # 玩家死亡，處理下一個玩家
                    
            collision_list = player.get_collision_with()
            for collision in collision_list:
                if collision_handler.check_is_entities(collision): # 假設 falling_rock 屬於 entities
                    player.add_reward_per_step(self.collision_falling_rock)

class PlayerFallingRockNearReward(RewardComponent):
    """
    當玩家朝著最近的落石移動時，根據其接近速度給予獎勵。
    如果玩家遠離落石前沒有與其碰撞，則給予懲罰。
    """
    
    def calculate(self, 
                  players: list['Player'], 
                  falling_rocks: list['FallingRock'], 
                  collision_handler: 'CollisionHandler', 
                  **kwargs
                 ):
        
        if not falling_rocks:
            return # 如果沒有石頭，不計算獎勵

        for player in players:
            if not player.get_is_alive():
                continue

            player_pos = pymunk.Vec2d(*player.get_position())
            player_vel = pymunk.Vec2d(*player.get_velocity())

            # 1. 找到距離玩家最近的石頭
            closest_rock = None
            min_dist_sq = float('inf')
            for rock in falling_rocks:
                rock_pos = pymunk.Vec2d(*rock.get_position())
                dist_sq = player_pos.get_dist_sqrd(rock_pos)
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_rock = rock
            
            if not closest_rock:
                continue

            # 2. 計算玩家相對於最近石頭的向量和速度
            rock_pos = pymunk.Vec2d(*closest_rock.get_position())
            
            # 向量：從玩家指向石頭
            direction_to_rock = rock_pos - player_pos

            # 3. 計算徑向速度 (玩家速度在朝向石頭方向上的分量)
            # 這是玩家速度向量在相對位置向量上的投影
            # 如果 direction_to_rock 的長度為 0，則不計算
            reward = 0

            

            if direction_to_rock.length > 0:
                # 我們只需要投影的純量值: player_vel · direction_to_rock / ||direction_to_rock||
                approach_velocity = player_vel.dot(direction_to_rock) / direction_to_rock.length
                
                # 4. 給予獎勵
                # 如果 approach_velocity > 0，表示玩家正在朝著石頭移動
                # 如果 approach_velocity < 0，表示玩家正在遠離石頭
                # 我們希望在靠近時給予正獎勵
                if approach_velocity > 0:
                    reward = approach_velocity
                    
                    # 為了防止獎勵值過大，可以進行縮放或裁剪
                    # 例如，將獎勵縮放到一個合理的範圍
                    reward *= self.falling_rock_near_proportion
                    if direction_to_rock.length < self.falling_rock_near_distance_threshold:
                        reward *= self.falling_rock_near_distance_reward_multiplier

                    if not player.get_special_status("stay_away_from_falling_rock_without_collision"):
                        collision_type = player.get_last_collision_with() # Reset last collision to avoid multiple penalty
                        rock = collision_handler.get_entity_from_collision_type(collision_type)
                        if rock is not None:
                            player.set_special_status("stay_away_from_falling_rock_without_collision", True)
                
                else:
                    if not player.get_special_status("stay_away_from_falling_rock_without_collision"):
                        collision_type = player.get_last_collision_with() # Reset last collision to avoid multiple penalty
                        rock = collision_handler.get_entity_from_collision_type(collision_type)
                        
                        if rock is None and player_pos.x != player.get_default_position()[0]:
                            player.set_special_status("stay_away_from_falling_rock_without_collision", True)
                            reward = self.stay_away_from_falling_rock_without_collision
                
                player.add_reward_per_step(reward)
                    