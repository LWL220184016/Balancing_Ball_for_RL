import math
import pymunk

from role.abilities.ability import Ability

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from script.role.player import Player

class Turning_topdown_viewing_angle(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)\

    def action(self, action_value, player: 'Player', current_step: int):
        
        if len(action_value) == 1: 
            player.shape.body.angle = action_value[0] * math.pi
        else: 
            x, y = player.get_position()
            
            dx = action_value[0] - x
            dy = action_value[1] - y
            angle = math.atan2(dy, dx)
            player.shape.body.angle = angle
        
    def human_control_interface(self, keyboard_keys, mouse_buttons, mouse_position):

        
        # # 計算向量差 (目標座標 - 角色座標)
        # dx = mouse_position[0] - body.position.x
        # dy = mouse_position[1] - body.position.y
        
        # # 使用 atan2 取得弧度 (y, x)
        # angle = math.atan2(dy, dx)
        return mouse_position
    
    def reset(self):
        return super().reset()