
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.role.player import Player
    from game.role.roles import Role
    from game.collision_handle import CollisionHandler

class RewardComponent(ABC):
    """所有獎勵計算元件的抽象基底類別"""
    def __init__(self, reward_parameters: dict):
        self.params = reward_parameters

        # define reward parameters
        for key, value in reward_parameters.items():
            setattr(self, key, value)

    @abstractmethod
    def calculate(self, players: list['Player'], collision_handler: 'CollisionHandler', **kwargs):
        """
        計算此元件負責的獎勵，並直接修改傳入的 player 物件。
        使用 **kwargs 來接收未來可能需要的額外資訊 (如 entities, alive_count 等)。
        """
        pass


class RewardCalculator:
    """協調多個獎勵元件來計算總獎勵"""

    def __init__(self, 
                 players: list['Player'] = None, 
                 platforms: list['Role'] = None,
                 entities: list['Role'] = None,
                 collision_handler: 'CollisionHandler' = None,
                 reward_components: list[RewardComponent] = None, # 接收一個元件列表
                 window_x: int = None, 
                 window_y: int = None
                ):
        self.players = players
        self.platforms = platforms
        self.entities = entities
        self.collision_handler = collision_handler
        self.reward_components = reward_components
        self.window_x = window_x
        self.window_y = window_y
        self.num_players = len(players)

    def calculate_rewards(self) -> tuple[list[float], bool]:
        """
        執行所有已註冊的獎勵元件，計算總獎勵，並判斷遊戲是否結束。
        """
        # 1. 重設每個玩家的單步獎勵
        for player in self.players:
            player.set_reward_per_step(0)

        # 2. 遍歷並執行所有獎勵元件
        for component in self.reward_components:
            component.calculate(
                players=self.players,
                falling_rocks=self.entities, # 假設 entities 是 falling_rocks 
                collision_handler=self.collision_handler,
                window_x=self.window_x,
                window_y=self.window_y # 透過 kwargs 傳遞額外參數
            )

        # 3. 收集結果並檢查遊戲狀態
        rewards = []
        alive_count = 0
        for player in self.players:
            rewards.append(player.get_reward_per_step())
            if player.get_is_alive():
                alive_count += 1
        
            
        return rewards, alive_count


