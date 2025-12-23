import pygame
import pymunk

from role.abilities.ability import Ability
from role.movable_object import MovableObjectFactory, MovableObject
from game_config import GameConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game.role.player import Player

class Shoot(Ability):
    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._keyboard_action = self.control_keys["keyboard"].get("action", [])
        self._mouse_action = self.control_keys["mouse"].get("action", [])
        self.bullet_factory = MovableObjectFactory()
        self.bullet_config = GameConfig.ABILITIES_OBJECTS_CONFIGS.get("bullet", None)
        if not self.bullet_config:
            raise ValueError("配置錯誤：在 abilities_objects_configs 中找不到 'bullet' 的定義")

    def action(self, action_value: tuple[float, float], player: 'Player', current_step: int):
            
        if self.check_is_ready(current_step):
            self.set_last_used_step(current_step)
            x, y = player.get_position()
            target_x, target_y = action_value
            self.bullet_config['default_position'] = (x, y)

            new_bullet = self.bullet_factory.create_movableObject(
                space=player.space,
                **self.bullet_config,
            )
            new_bullet.set_owner(player)

            # 計算方向向量
            direction_vector = pymunk.Vec2d(target_x - x, target_y - y)

            # 只有在向量長度不為零時才進行計算，以避免除以零的錯誤
            if direction_vector.length > 0:
                # 正規化向量（使其長度為1）並乘以速度
                velocity_vector = direction_vector.normalized() * self.speed
                # 直接設置速度
                new_bullet.set_velocity(velocity_vector)

    def human_control_interface(self, keyboard_keys, mouse_buttons):
        if self._is_pressed(self._keyboard_action, self._mouse_action, keyboard_keys, mouse_buttons):
            p1_ability1 = pygame.mouse.get_pos()  # Activate ability 1
            return p1_ability1
        return None

    def reset(self):
        return super().reset()