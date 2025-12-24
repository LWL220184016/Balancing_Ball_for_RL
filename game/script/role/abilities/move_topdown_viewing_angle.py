import pygame
import pymunk

from role.abilities.ability import Ability

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from script.role.player import Player

class Move_topdown_viewing_angle(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._keyboard_front = self.control_keys["keyboard"].get("front", [])
        self._keyboard_left = self.control_keys["keyboard"].get("left", [])
        self._keyboard_back = self.control_keys["keyboard"].get("back", [])
        self._keyboard_right = self.control_keys["keyboard"].get("right", [])

        self._mouse_front = self.control_keys["mouse"].get("front", [])
        self._mouse_left = self.control_keys["mouse"].get("left", [])
        self._mouse_back = self.control_keys["mouse"].get("back", [])
        self._mouse_right = self.control_keys["mouse"].get("right", [])

    def action(self, action_value: tuple[float, float], player: 'Player', current_step: int):
        if action_value == (0, 0): 
            return
        
        if self.check_is_ready(current_step):
            self.set_last_used_step(current_step)
            force_vector = pymunk.Vec2d(action_value[0] * self.force, action_value[1] * self.force)
            player.apply_force_at_world_point(force_vector, player.get_position())

    def human_control_interface(self, keyboard_keys, mouse_buttons):
        # 使用 bool 的整數特性 (True=1, False=0)

        move_front = self._is_pressed(self._keyboard_front, self._mouse_front, keyboard_keys, mouse_buttons)
        move_left = self._is_pressed(self._keyboard_left, self._mouse_left, keyboard_keys, mouse_buttons)
        move_back = self._is_pressed(self._keyboard_back, self._mouse_back, keyboard_keys, mouse_buttons)
        move_right = self._is_pressed(self._keyboard_right, self._mouse_right, keyboard_keys, mouse_buttons)

        # 如果同時按下，-1 + 1 = 0 (原地不動)，更符合玩家直覺
        x_force = move_right - move_left 
        y_force = -(move_front - move_back)

        return x_force, y_force
    
    def reset(self):
        return super().reset()