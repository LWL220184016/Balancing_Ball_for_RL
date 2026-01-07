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
            player.shape.body.angular_velocity = action_value[0] * self.speed
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

    def bot_action(self, self_role_id: str, players: list['Player'], **kwargs):
        """
        返回距離自己最近的敵人的坐標
        
        :param self_role_id: 自己的角色 ID
        :type self_role_id: str
        :param players: 所有玩家的物件列表 (假設物件有 team_id, hp, role_id 屬性及 get_position() 方法)
        :type players: list
        :param kwargs: 其他參數
        :return: 最近敵人的坐標 (x, y) 或 None (若無敵人)
        """
        
        self_pos = None
        enemy_pos = []
        
        for p in players:
            if p.role_id == self_role_id:
                self_pos = p.get_position()
            else:
                enemy_pos.append(p.get_position())
        
        if self_pos is None:
            return None

        closest_enemy_pos = None
        min_distance = float('inf') # 設定為無限大

        for pos in enemy_pos:
            
            # 計算距離 (使用歐幾里得距離)
            distance = math.dist(self_pos, pos)

            if distance < min_distance:
                min_distance = distance
                closest_enemy_pos = pos
        return closest_enemy_pos

    def reset(self):
        return super().reset()