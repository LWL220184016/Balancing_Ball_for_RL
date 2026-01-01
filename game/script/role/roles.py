import time
import pymunk
import numpy as np

from abc import ABC, abstractmethod
from typing import Dict
from role.abilities.ability import Ability
from role.shapes.shape import Shape
from role.abilities import *  # Import all abilities 

class Role(ABC):

    @abstractmethod
    def __init__(self, 
                 role_id: str = None,
                 is_alive: bool = None,
                 shape: Shape = None, 
                 space: pymunk.Space = None, 
                 color: tuple = None, 
                 abilities: list[str] = None, 
                 health: int | str = None,
                 owner: 'Role' = None,
                 expired_time: float = None
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
        
        self.role_id: str = role_id
        self.is_alive = is_alive
        self.is_Role_sub_class = True  # 用於標記這是一個 Role 類別的實例，防止 isinstance 路徑誤判以及循環引用
        self.shape = shape
        self.space = space
        self.color = color
        self.color_rl = color
        self.collision_with = []
        self.last_collision_with = -1  # 用於記錄最後一次碰撞的類型，會在 add_collision_with 中更新
        self.health = health  # 初始生命值
        self.default_health = health  # 用於重置生命值
        self.expired_time = expired_time  # 用於標記角色的過期時間 (time * fps)

        # 使用列表推導式和 globals() 來動態實例化類別
        # name = "Role" if role_id == None else role_id
        # print(f"Initializing {name} with abilities: {abilities}")
        if abilities:
            self.abilities: Dict[str, Ability] = {name: globals()[name]() for name in abilities if name in globals()}
            # print(f"Initialized Role with abilities: {list(self.abilities.keys())}")
        else:
            self.abilities: Dict[str, Ability] = {}

    def perform_action(self, action: dict, current_step: int):
        """
        根據 action 字典和 self.abilities 執行對應動作。
        action 格式範例: {"Move": 1, "Jump": 0, "Collision": (0.5, 0.5)}
        """

        # 用於儲存能力產生的物件 (比如子彈，屏障)
        ability_generated_objects: list[Role] = []

        # 遍歷玩家擁有的所有能力
        for ability_name, action_data in action.items():
            # 從 action 字典中獲取對應的數據
            ability_instance = self.abilities[ability_name]

            if action_data is not None:
                data = ability_instance.action(action_data, self, current_step)
                if getattr(data, 'is_Role_sub_class', False):
                    ability_generated_objects.append(data)

        return ability_generated_objects
                    
    @abstractmethod
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

    @abstractmethod
    def get_state(self, window_size: tuple, velocity_scale: float):
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
        # ---------------------------------------------
        vel_x, vel_y = self.get_velocity()
        # 使用 tanh 進行正規化，velocity_scale 是一個超參數，用於調整靈敏度
        norm_vx = np.tanh(vel_x / velocity_scale)
        norm_vy = np.tanh(vel_y / velocity_scale)

        # ---------------------------------------------
        is_colliding = 1.0 if self.get_collision_with() else 0.0

        # ---------------------------------------------
        current_time = time.time()
        ability_cooldown = {}
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
            
            ability_cooldown[ability.get_name()] = normalized_cooldown

            
        state = {"pos": [norm_x, norm_y], 
                # ---------------------------------------------
                 "vel": [norm_vx, norm_vy],
                # ---------------------------------------------
                 "is_colliding": is_colliding,
                # ---------------------------------------------
                 "ability_cooldown": ability_cooldown
                }

        return state

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

    def check_ability_ready(self, ability_name: str, current_step: int) -> bool:
        ability = self.abilities.get(ability_name)
        if ability:
            return ability.check_is_ready(current_step)
        return False

    def add_to_space(self):
        body, shape = self.shape.get_physics_components()
        self.space.add(body, shape)

    def remove_from_space(self):
        body, shape = self.shape.get_physics_components()
        self.space.remove(body, shape)
    
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
    
    def get_abilities(self):
        return self.abilities
    
    def get_ability_cooldown(self, ability_name: str) -> float | None:
        ability = self.abilities.get(ability_name)
        if ability:
            return ability.get_cooldown()
        return None

    def set_position_absolute_value(self, position: tuple):
        self.shape.set_position_absolute_value(position)

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

