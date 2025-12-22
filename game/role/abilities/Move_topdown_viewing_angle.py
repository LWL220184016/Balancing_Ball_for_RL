import pygame
import pymunk

from role.abilities.ability import Ability

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game.role.player import Player

class Move_topdown_viewing_angle(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)

    def action(self, action_value: float, player: 'Player', current_step: int):
            
        if self.check_is_ready(current_step):
            self.set_last_used_step(current_step)
            force_vector = pymunk.Vec2d(action_value * self.force, 0)
            player.apply_force_at_world_point(force_vector, player.get_position())

    def human_control_interface(self, keyboard_keys, mouse_buttons):
        return None
    
    def reset(self):
        return super().reset()