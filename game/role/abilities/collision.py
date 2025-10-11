import pymunk
# 1. 導入 TYPE_CHECKING
from typing import TYPE_CHECKING

from role.abilities.ability import Ability

# 2. 建立一個只在類型檢查時才會執行的區塊
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from game.role.player import Player

class Collision(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)

    def action(self, action_value: tuple[float, float], player: 'Player', current_step: int):
            
        if self.check_is_ready(current_step):
            self.set_last_used_step(current_step)
            # 处理旋转动作
            # 即使使用了字串提示，IDE 仍然可以正確提供代碼導航和自動完成
            x, y = player.get_position()
            target_x, target_y = action_value

            # 計算方向向量
            direction_vector = pymunk.Vec2d(target_x - x, target_y - y)

            # 只有在向量長度不為零時才進行計算，以避免除以零的錯誤
            if direction_vector.length > 0:
                # 正規化向量（使其長度為1）並乘以速度
                velocity_vector = direction_vector.normalized() * self.speed
                # 直接設置速度
                player.set_velocity(velocity_vector)

    def reset(self):
        return super().reset()