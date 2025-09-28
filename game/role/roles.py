import time
import pygame
import pymunk

from typing import Dict
from role.abilities.ability import Ability
from role.shapes.shape import Shape
from role.abilities import *  # Import all abilities 

class Role:
    def __init__(self, shape: Shape, color: tuple, abilities: list[str]):
        self.shape = shape
        self.color = color
        # 使用列表推導式和 globals() 來動態實例化類別
        if abilities:
            self.abilities: Dict[str, Ability] = {name: globals()[name]() for name in abilities if name in globals()}
            print(f"Initialized Role with abilities: {list(self.abilities.keys())}")
        else:
            self.abilities = {}
            print("Initialized with no abilities.")

    def perform_action(self, players_action: list):
        raise NotImplementedError(f"This method '{self.perform_action.__name__}' should be overridden by subclasses.")

    def _draw_indie_style(self, screen: pygame.Surface):
        self.shape._draw(screen, self.color)

    def reset(self, space: pymunk.Space):
        self.shape.reset()

        if self.abilities:
            for ability in self.abilities.values():
                ability.reset()
        body = self.shape.get_physics_components()[0]
        space.reindex_shapes_for_body(body)

    def get_state(self, window_size: tuple):
        """
        返回該角色的正規化狀態向量。
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
            last_use_time = ability.get_last_used_time()

            if cooldown_duration > 0:
                time_since_last_use = current_time - last_use_time
                remaining_cooldown = max(0, cooldown_duration - time_since_last_use)
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
    
    def get_velocity(self):
        return self.shape.get_velocity()
    
    def get_angular_velocity(self):
        return self.shape.get_angular_velocity()

    def get_physics_components(self):
        """Returns the physics body and shape for adding to the space."""
        return self.shape.get_physics_components()
    
    def set_angular_velocity(self, angle: float):
        self.shape.set_angular_velocity(angle)
