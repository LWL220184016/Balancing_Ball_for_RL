import pymunk
# 1. 導入 TYPE_CHECKING
from typing import TYPE_CHECKING

from role.abilities.ability import Ability

# 2. 建立一個只在類型檢查時才會執行的區塊
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from game.role.player import Player

class Jump(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)

    def action(self, action_value: float, player: 'Player', current_step: int):
            
        if self.check_is_ready(current_step) and player.get_is_on_ground():
            self.set_last_used_step(current_step)
            force_vector = pymunk.Vec2d(0, action_value * self.force)
            player.apply_force_at_world_point(force_vector, player.get_position())

    def reset(self):
        return super().reset()