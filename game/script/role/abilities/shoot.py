import pygame
import pymunk
import copy

from role.abilities.ability import Ability
from role.ability_generated_object_factory import AbilityGeneratedObjectFactory
from role.movable_object import MovableObject
from script.game_config import GameConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from script.role.player import Player

class Shoot(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._keyboard_action = self.control_keys["keyboard"].get("action", [])
        self._mouse_action = self.control_keys["mouse"].get("action", [])

        self.ability_generated_object_name = "bullet"

        if self.ability_generated_object_config == None:
            _ability_generated_object_cfg = GameConfig.ABILITIES_OBJECTS_CONFIGS.get(self.ability_generated_object_name, None)
            self.ability_generated_object_config = copy.deepcopy(_ability_generated_object_cfg)
            self.ability_generated_object_config["expired_time"] = _ability_generated_object_cfg.get("expired_time", None) * GameConfig.FPS if _ability_generated_object_cfg.get("expired_time", None) else None
            # print('self.ability_generated_object_config["expired_time"]: ', self.ability_generated_object_config["expired_time"])

            if not self.ability_generated_object_config:
                raise ValueError(f"配置錯誤：在 abilities_objects_configs 中找不到 '{self.ability_generated_object_name}' 的定義")
            self.collision_type_bullet = GameConfig.get_collision_type(self.ability_generated_object_name)
            self.bullet_factory = AbilityGeneratedObjectFactory()

    def action(self, action_value: int, player: 'Player', current_step: int):
        if action_value <= 0: 
            return
            
        if not self.check_is_ready(current_step):
            return
        
        self.set_last_used_step(current_step)
        
        x, y = player.get_position()
        facing_angle = player.shape.body.angle 

        collision_type = player.get_collision_type() + self.collision_type_bullet
        new_bullet = self.bullet_factory.create_role(
                space=player.space, 
                role_id=f"bullet", 
                is_alive=True,
                body=pymunk.Body.DYNAMIC,
                collision_type_role=collision_type,
                cls=MovableObject,
                **self.ability_generated_object_config
            ) 
        
        new_bullet.set_position_absolute_value((x, y))
        new_bullet.shape.body.angle = facing_angle
        new_bullet.add_to_space()

        velocity_vector = pymunk.Vec2d(1, 0).rotated(facing_angle) * self.speed
        new_bullet.set_velocity(velocity_vector)

        return new_bullet

    def human_control_interface(self, keyboard_keys, mouse_buttons, mouse_position):
        if self._is_pressed(self._keyboard_action, self._mouse_action, keyboard_keys, mouse_buttons):
            return 1
        return 0
    
    def reset(self):
        return super().reset()