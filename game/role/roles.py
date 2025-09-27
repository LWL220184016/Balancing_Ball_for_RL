

import time
from role.shapes.shape import Shape

class Role:
    def __init__(self, shape: Shape, color: tuple, action_params: dict, action_cooldown: dict):
        self.shape = shape
        self.color = color
        self.action_cooldown = action_cooldown  # Dictionary of action cooldowns
        self.action_params = action_params  # Dictionary of action parameters
        self.last_action_time = {action: 0 for action in action_cooldown}  # Track last action time for each action

    def move(self, direction):
        raise NotImplementedError(f"This method '{self.move.__name__}' should be overridden by subclasses.")

    def perform_action(self, players_action):
        raise NotImplementedError(f"This method '{self.perform_action.__name__}' should be overridden by subclasses.")

    def _draw_indie_style(self, screen):
        self.shape._draw(screen, self.color)

    def check_cooldowns(self, ability_name) -> bool:
        """Check and update action cooldowns"""
        
        if (time.time() - self.last_action_time[ability_name]) > self.action_cooldown[ability_name]:
            self.last_action_time[ability_name] = time.time()
            return True
        return False

    def reset(self, space):
        self.shape.reset()
        self.last_action_time = {action: 0 for action in self.action_cooldown}
        body = self.shape.get_physics_components()[0]
        space.reindex_shapes_for_body(body)

    def get_state(self, window_size):
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
        sorted_actions = sorted(self.action_cooldown.keys())

        for action in sorted_actions:
            cooldown_duration = self.action_cooldown.get(action, 0)
            last_use_time = self.last_action_time.get(action, 0)

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
    
    def set_angular_velocity(self, angle):
        self.shape.set_angular_velocity(angle)
