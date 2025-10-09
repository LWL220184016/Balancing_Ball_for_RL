import time
import pygame
import pymunk

from typing import Dict
from role.abilities.ability import Ability
from role.shapes.shape import Shape
from role.abilities import *  # Import all abilities 

class Role:
    def __init__(self, 
                 shape: Shape = None, 
                 space: pymunk.Space = None, 
                 color: tuple = None, 
                 abilities: list[str] = None, 
                 health: int | str = None
                ):
        """
        Base class for all roles.

        Args:
            shape (Shape): The shape object representing the role's physical form.
            space (pymunk.Space): The physics space where the role exists.
            color (tuple): RGB color of the role for rendering.
            abilities (list[str]): List of ability class names as strings to be assigned to the role.
            health (int | str): Initial health of the role. Will be infinite health if it is a string.
        """


        self.shape = shape
        self.space = space
        self.color = color
        self.collision_with = []
        self.last_collision_with = -1  # 用於記錄最後一次碰撞的類型，會在 add_collision_with 中更新
        self.health = health  # 初始生命值
        self.default_health = health  # 用於重置生命值

        # 使用列表推導式和 globals() 來動態實例化類別
        if abilities:
            self.abilities: Dict[str, Ability] = {name: globals()[name]() for name in abilities if name in globals()}
            print(f"Initialized Role with abilities: {list(self.abilities.keys())}")
        else:
            self.abilities = {}

    def perform_action(self, action: list):
        raise NotImplementedError(f"This method '{self.perform_action.__name__}' should be overridden by subclasses.")

    def _draw_indie_style(self, screen: pygame.Surface):
        self.shape._draw(screen, self.color)

    def reset(self, health: int = None):
        self.shape.reset()
        self.set_collision_with([])
        self.set_last_collision_with(-1)
        self.set_health(health if health is not None else self.default_health)

        if self.abilities:
            for ability in self.abilities.values():
                ability.reset()
        body = self.shape.get_physics_components()[0]
        self.space.reindex_shapes_for_body(body)

    def add_collision_with(self, collision_with: int):
        self.collision_with.append(collision_with)
        self.last_collision_with = collision_with

    def increase_health(self, amount: int = 1) -> bool:
        """
        嘗試增加生命值。

        Args:
            amount (int): 增加的生命值數量。

        Returns:
            bool: 如果生命值是數字並成功增加，返回 True；如果生命值不是數字 (例如 'infinite'），返回 False。
        """

        if isinstance(self.get_health(), int):
            self.health += amount
            return True # True mean health is number
        return False # False mean health is not number (e.g., 'infinite')

    def decrease_health(self, amount: int = 1) -> bool:
        """
        嘗試減少生命值。
        
        Args:
            amount (int): 減少的生命值數量。

        Returns:
            bool: 如果生命值是數字並成功減少，返回 True；如果生命值不是數字 (例如 'infinite'），返回 False。
        """
        
        if isinstance(self.get_health(), int):
            self.health -= amount
            return True # True mean health is number
        return False # False mean health is not number (e.g., 'infinite')

    def get_state(self, window_size: tuple):
        """
        返回該角色的正規化狀態向量。
        Args:
            window_size (tuple): The size of the game window for normalizing position.
        Returns:
            list: A list representing the normalized state of the role, including position and ability cooldowns
        """

        win_x, win_y = window_size
        pos_x, pos_y = self.get_position()

        norm_x = pos_x / win_x * 2 - 1
        norm_y = pos_y / win_y * 2 - 1

        state = [norm_x, norm_y]

        current_time = time.time()
        # 確保按鍵順序一致，以便狀態向量的維度固定

        for ability in self.abilities.values():
            cooldown_duration = ability.get_cooldown()
            last_used_step = ability.get_last_used_step()

            if cooldown_duration > 0 and last_used_step is not None:
                step_since_last_use = current_time - last_used_step
                remaining_cooldown = max(0, cooldown_duration - step_since_last_use)
                # 正規化到 [0, 1] 範圍
                normalized_cooldown = remaining_cooldown / cooldown_duration
            else:
                # 如果沒有冷卻時間，則始終為 0 (可用)
                normalized_cooldown = 0.0
            
            state.append(normalized_cooldown)

        return state

    def get_color(self):
        return self.color
    
    def get_size(self):
        return self.shape.get_size()
    
    def get_collision_type(self):
        return self.shape.get_collision_type()
    
    def get_position(self):
        return self.shape.get_position()
    
    def get_default_position(self):
        return self.shape.get_default_position()
    
    def get_physics_components(self):
        """Returns the physics body and shape for adding to the space."""
        return self.shape.get_physics_components()
    
    def get_velocity(self):
        return self.shape.get_velocity()
    
    def get_angular_velocity(self):
        return self.shape.get_angular_velocity()

    def get_is_alive(self):
        return self.is_alive

    def get_is_on_ground(self):
        return self.is_on_ground

    def get_collision_with(self):
        return self.collision_with

    def get_last_collision_with(self):
        return self.last_collision_with
    
    def get_health(self):
        return self.health

    def set_velocity(self, velocity: pymunk.Vec2d):
        self.shape.set_velocity(velocity)

    def set_angular_velocity(self, angle: float):
        self.shape.set_angular_velocity(angle)

    def set_is_alive(self, alive_status: bool):
        self.is_alive = alive_status

    def set_is_on_ground(self, on_ground: bool):
        self.is_on_ground = on_ground

    def set_collision_with(self, collision_with: list[int]):
        self.collision_with = collision_with

    def set_last_collision_with(self, collision_with: int):
        self.last_collision_with = collision_with

    def set_health(self, health: int):
        self.health = health