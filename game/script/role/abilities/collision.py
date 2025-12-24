import pygame
import pymunk

from role.abilities.ability import Ability

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game.role.player import Player

class Collision(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._keyboard_action = self.control_keys["keyboard"].get("action", [])
        self._mouse_action = self.control_keys["mouse"].get("action", [])

    def action(self, action_value: tuple[float, float], player: 'Player', current_step: int):
            
        if self.check_is_ready(current_step):
            self.set_last_used_step(current_step)
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

    def human_control_interface(self, keyboard_keys, mouse_buttons):
        if self._is_pressed(self._keyboard_action, self._mouse_action, keyboard_keys, mouse_buttons):
            p1_ability1 = pygame.mouse.get_pos()  # Activate ability 1
            return p1_ability1
        return None

    def reset(self):
        return super().reset()