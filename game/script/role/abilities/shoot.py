import pygame
import pymunk
import copy

from role.abilities.ability import Ability
from role.movable_object import MovableObjectFactory, MovableObject
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

            if not self.ability_generated_object_config:
                raise ValueError(f"配置錯誤：在 abilities_objects_configs 中找不到 '{self.ability_generated_object_name}' 的定義")
            collision_type_bullet = GameConfig.get_collision_type(self.ability_generated_object_name)
            self.bullet_factory = MovableObjectFactory(collision_type_bullet)
            self.ability_generated_object_config["expired_time"] = _ability_generated_object_cfg.get("expired_time", None) * GameConfig.FPS if _ability_generated_object_cfg.get("expired_time", None) else None
            # print('self.ability_generated_object_config["expired_time"]: ', self.ability_generated_object_config["expired_time"])

    def action(self, action_value: tuple[float, float], player: 'Player', current_step: int):
            
        if self.check_is_ready(current_step):
            self.set_last_used_step(current_step)
            x, y = player.get_position()
            target_x, target_y = action_value

            new_bullet = self.bullet_factory.create_movableObject(
                role_id="bullet",
                space=player.space,
                **self.ability_generated_object_config,
            )
            new_bullet.set_owner(player)
            new_bullet.set_position_absolute_value((x, y))
            new_bullet.add_to_space()

            # 計算方向向量
            direction_vector = pymunk.Vec2d(target_x - x, target_y - y)

            # 只有在向量長度不為零時才進行計算，以避免除以零的錯誤
            if direction_vector.length > 0:
                # 正規化向量（使其長度為1）並乘以速度
                velocity_vector = direction_vector.normalized() * self.speed
                # 直接設置速度
                new_bullet.set_velocity(velocity_vector)

            return new_bullet

    def human_control_interface(self, keyboard_keys, mouse_buttons, mouse_position):
        if self._is_pressed(self._keyboard_action, self._mouse_action, keyboard_keys, mouse_buttons):
            if mouse_position:
                return mouse_position
            mouse_position = pygame.mouse.get_pos()  # Activate ability 1
            return mouse_position
        return None

    def reset(self):
        return super().reset()