import pymunk
from levels.rewards.reward_calculator import RewardComponent, terminates_round

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from script.role.player import Player
    from script.role.movable_object import MovableObject
    from script.collision_handle import CollisionHandler

@terminates_round
class PlayerFallingRockCollisionReward(RewardComponent):
    """處理與實體 (如落石) 的碰撞獎勵/懲罰"""
    def calculate(self, 
                  players: list['Player'], 
                  falling_rocks: list['MovableObject'], 
                  collision_handler: 'CollisionHandler', 
                  window_x: int, 
                  window_y: int,
                  **kwargs
                 ):
                  
        
        penalty = 0
        decrease_health = False
        for rock in falling_rocks:
            if rock.get_is_on_ground():
                penalty = self.falling_rock_fall_on_platform
                decrease_health = True
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
            if decrease_health:
                if self._terminates_round:
                    if player.decrease_health(1) and player.get_health() <= 0:
                        player.set_is_alive(False)
                        continue  # 玩家死亡，處理下一個玩家
                    
            collision_list = player.get_collision_with()
            for collision in collision_list:
                if collision_handler.check_is_entities(collision) and not player.get_special_status("collision_falling_rock"): # 假設 falling_rock 屬於 entities
                    player.add_reward_per_step(self.collision_falling_rock)
                    player.set_special_status("collision_falling_rock", True)

class PlayerFallingRockNearReward(RewardComponent):
    """
    當玩家朝著最近的落石移動時，根據其接近速度給予獎勵。
    如果玩家遠離落石前沒有與其碰撞，則給予懲罰。
    """
    
    def calculate(self, 
                  players: list['Player'], 
                  falling_rocks: list['MovableObject'], 
                  **kwargs
                 ):
        
        if not falling_rocks:
            return
        
        for player in players:
            if not player.get_is_alive():
                continue

            player_pos = pymunk.Vec2d(*player.get_position())

            # 找到最近的落石
            min_dist = float('inf')
            for rock in falling_rocks:
                rock_pos = pymunk.Vec2d(*rock.get_position())
                dist = player_pos.get_distance(rock_pos)
                if dist < min_dist:
                    min_dist = dist

            # 超出距離閾值就不給獎勵
            if min_dist > self.falling_rock_near_distance_threshold:
                continue

            # 根據距離線性給獎勵：越近越大
            proximity_factor = max(0.0, 1.0 - (min_dist / self.falling_rock_near_distance_threshold))
            reward = proximity_factor * self.falling_rock_near_proportion
            player.add_reward_per_step(reward)
                    
