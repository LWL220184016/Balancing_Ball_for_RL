
import time
import pymunk


class Player:
    def __init__(self, shape, ball_color, action_params, action_cooldown):
        self.shape = shape
        self.ball_color = ball_color
        self.action_cooldown = action_cooldown  # Dictionary of action cooldowns
        self.action_params = action_params  # Dictionary of action parameters
        self.last_action_time = {action: 0 for action in action_cooldown}  # Track last action time for each action

    def move(self, direction):
        
        pass

    def jump(self):
        pass


    def perform_action(self, players_action: list = []):
        # 遍歷所有玩家
        for i, player_body in enumerate(self.dynamic_body_players):
            if players_action[i][1] > 0:  # Jump action
                if time.time() - self.players_action_lasttime[i]["jump"] > self.players_action_cooldown[i]["jump"]:
                    players_action[i][1] * self.players_action_params[i]["jump"]

            force_vector = pymunk.Vec2d(players_action[i][0], players_action[i][1])
            player_body.apply_force_at_world_point(force_vector, player_body.position)

            # # 施加角速度
            # player_body.angular_velocity += action_value
            # self.dynamic_body_players[1].angular_velocity += p1action