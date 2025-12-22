import pygame

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from balancing_ball_game import BalancingBallGame

class HumanControl:
    def __init__(self, game: 'BalancingBallGame'):
        self.game = game
        # 獲取玩家及其能力字典
        self.player = self.game.get_players()[0]
        self.abilities = self.player.get_abilities() 

    def get_player_actions(self) -> dict:
        """
        這是一個通用的方法，自動遍歷所有能力並獲取其輸入
        """
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game.get_game_over():
                    self.game.reset()
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        action_dict = {}

        for name, ability_instance in self.abilities.items():
            act_value = ability_instance.human_control_interface(keys, mouse_buttons)
            
            if act_value is not None and act_value != 0:
                action_dict[name] = act_value

        return action_dict