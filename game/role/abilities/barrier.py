import pymunk
# 1. 導入 TYPE_CHECKING
from typing import TYPE_CHECKING

from role.abilities.ability import Ability

# 2. 建立一個只在類型檢查時才會執行的區塊
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from game.role.player import Player

class Barrier(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)

    def action(self, action_value: tuple[float, float], player: 'Player'):
            
        if self.check_cooldowns():
            # TODO 生成并在持續時間内保持一個靜止的長方體，
            # 该长方体应具有碰撞属性以阻挡其他物体
            # 第一個 Float 是相較於玩家自身的角度(以玩家為圓形中心正上方為0度)，最大 360 最小 0
            # 第二個 Float 是長方體的傾斜角度，最大 360 最小 0

            pass


    def reset(self):
        return super().reset()