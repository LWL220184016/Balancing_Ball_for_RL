import pygame
import pymunk

from role.abilities.ability import Ability

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game.role.player import Player

class Move_horizontal_viewing_angle(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._keyboard_left = self.control_keys["keyboard"].get("left", [])
        self._keyboard_right = self.control_keys["keyboard"].get("right", [])
        self._mouse_left = self.control_keys["mouse"].get("left", [])
        self._mouse_right = self.control_keys["mouse"].get("right", [])

    def action(self, action_value: float, player: 'Player', current_step: int):
        if action_value == 0: 
            return
        
        if self.check_is_ready(current_step):
            self.set_last_used_step(current_step)
            force_vector = pymunk.Vec2d(action_value * self.force, 0)
            player.apply_force_at_world_point(force_vector, player.get_position())

    def human_control_interface(self, keyboard_keys, mouse_buttons):
        # 使用 bool 的整數特性 (True=1, False=0)
        move_left = self._is_pressed(self._keyboard_left, self._mouse_left, keyboard_keys, mouse_buttons)
        move_right = self._is_pressed(self._keyboard_right, self._mouse_right, keyboard_keys, mouse_buttons)
        
        # 如果同時按下，-1 + 1 = 0 (原地不動)，更符合玩家直覺
        p1_x_force = move_right - move_left
        
        return p1_x_force

    def reset(self):
        return super().reset()
