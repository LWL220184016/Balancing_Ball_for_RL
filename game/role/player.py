
import pymunk


class Player:
    def __init__(self, shape, ball_color, action_params, action_cooldown):
        self.shape = shape
        self.ball_color = ball_color
        self.action_cooldown = action_cooldown  # Dictionary of action cooldowns
        self.action_params = action_params  # Dictionary of action parameters
        self.last_action_time = {action: 0 for action in action_cooldown}  # Track last action time for each action
        self.is_alive = True

    def move(self, direction):
        force_vector = pymunk.Vec2d(direction * self.action_params["speed"], 0)
        self.shape.body.apply_force_at_world_point(force_vector, self.shape.body.position)

        # # 施加角速度
        # self.shape.body.angular_velocity += p1action

    def jump(self, action):
        force_vector = pymunk.Vec2d(0, action * self.action_params["jump_high"])
        self.shape.body.apply_force_at_world_point(force_vector, self.shape.body.position)

    def perform_action(self, players_action):
        # 遍歷所有玩家
        if players_action[0] != 0:
            self.move(players_action[0])

        if players_action[1] != 0 and self.get_velocity()[1] == 0:  # Jump action
            self.jump(players_action[1])

    def _draw_indie_style(self, screen):
        self.shape._draw(screen, self.ball_color)

    def get_radius(self):
        return self.shape.shape_radio
    
    def get_color(self):
        return self.ball_color
    
    def get_position(self):
        return self.shape.body.position[0], self.shape.body.position[1]
    
    def get_default_position(self):
        return self.shape.default_position[0], self.shape.default_position[1]
    
    def get_velocity(self):
        return self.shape.body.velocity[0], self.shape.body.velocity[1]

    def get_physics_components(self):
        """Returns the physics body and shape for adding to the space."""
        return self.shape.body, self.shape.shape