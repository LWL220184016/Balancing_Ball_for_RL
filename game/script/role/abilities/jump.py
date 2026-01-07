import pygame
import pymunk

from role.abilities.ability import Ability

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from script.role.player import Player

class Jump(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._keyboard_action = self.control_keys["keyboard"].get("action", [])
        self._mouse_action = self.control_keys["mouse"].get("action", [])

    def action(self, action_value: float, player: 'Player', current_step: int):
            
        if self.check_is_ready(current_step) and player.get_is_on_ground():
            self.set_last_used_step(current_step)
            force_vector = pymunk.Vec2d(0, action_value * self.force)
            player.apply_force_at_world_point(force_vector, player.get_position())

    def human_control_interface(self, keyboard_keys, mouse_buttons, mouse_position):
        p1_y_force = 0
        if self._is_pressed(self._keyboard_action, self._mouse_action, keyboard_keys, mouse_buttons):
            p1_y_force = 1  # Jump force persentage (0 to 1)

        return p1_y_force
    
    def bot_action(self, **kwargs):
        return 1
    
    def reset(self):
        return super().reset()