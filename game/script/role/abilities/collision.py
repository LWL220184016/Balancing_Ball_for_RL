import pygame
import pymunk

from role.abilities.ability import Ability

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from script.role.player import Player

class Collision(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._keyboard_action = self.control_keys["keyboard"].get("action", [])
        self._mouse_action = self.control_keys["mouse"].get("action", [])

    def action(self, action_value: int, player: 'Player', current_step: int):
        if action_value != 1:
            return
        if not self.check_is_ready(current_step):
            return
            
        self.set_last_used_step(current_step)
        
        direction_vector = pymunk.Vec2d(1, 0).rotated(player.shape.body.angle)

        # 根據技能速度計算最終速度向量
        velocity_vector = direction_vector * self.speed
        player.set_velocity(velocity_vector)

    def human_control_interface(self, keyboard_keys, mouse_buttons, mouse_position):
        if self._is_pressed(self._keyboard_action, self._mouse_action, keyboard_keys, mouse_buttons):
            return 1
        return 0

    def reset(self):
        return super().reset()
    