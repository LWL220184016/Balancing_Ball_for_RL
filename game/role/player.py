import pymunk
import numpy as np

try:
    from role.roles import Role
    from role.shapes.circle import Circle
except ImportError:
    from game.role.roles import Role
    from game.role.shapes.circle import Circle

class Player(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_alive = True
        self.is_on_ground = False
        self.reward_per_step = 0  # 每一步的獎勵

    def perform_action(self, action: list):
        # 遍歷所有玩家，並使用 .get() 安全地檢查能力是否存在
        if action[0] != 0 and self.abilities.get("Move"):
            self.abilities["Move"].action(action[0], self)

        if action[1] != 0 and self.abilities.get("Jump"):
            self.abilities["Jump"].action(action[1], self)

        if isinstance(action[2], tuple) and self.abilities.get("Collision"):
            # 处理旋转动作
            self.abilities["Collision"].action(action[2], self)

    def get_state(self, window_size: tuple, velocity_scale: float = 200.0):
        """
        獲取玩家的正規化狀態。
        使用 tanh 函數來處理沒有固定上限的速度。
        velocity_scale: 用於調整速度的靈敏度。
        """
        # 首先，從父類獲取基本狀態（位置、技能冷卻等）
        state = super().get_state(window_size=window_size)

        # 接著，添加正規化的速度
        vel_x, vel_y = self.get_velocity()

        # 使用 tanh 進行正規化，velocity_scale 是一個超參數，用於調整靈敏度
        norm_vx = np.tanh(vel_x / velocity_scale)
        norm_vy = np.tanh(vel_y / velocity_scale)

        state.extend([norm_vx, norm_vy])

        return state

    def reset(self):
        super().reset()
        self.is_alive = True
        self.is_on_ground = False

    def apply_force_at_world_point(self, force: pymunk.Vec2d, point: tuple[float, float]):
        self.shape.apply_force_at_world_point(force, point)

    def get_reward_per_step(self):
        return self.reward_per_step
    
    def set_reward_per_step(self, reward: float):
        self.reward_per_step = reward
    
    def add_reward_per_step(self, reward: float):
        self.reward_per_step += reward

class PlayerFactory:
    def __init__(self, collision_type_player: int):
        self.collision_type_player = collision_type_player

    def create_player(self,
                      window_x: int = 1000,
                      window_y: int = 600,
                      space: pymunk.Space = None,
                      shape_type: str = "circle",
                      size: tuple = None,
                      shape_mass: float = None,
                      shape_friction: float = None,
                      shape_elasticity: float = None,
                      default_position: tuple = None,
                      default_velocity: tuple = None,
                      abilities: dict = None,
                      health: int | str = None,
                      color: tuple = None
                     ) -> Player:
        """Create the ball with physics properties.

        Args:
            window_x (int): Width of the game window.
            window_y (int): Height of the game window.
            shape_type (str): Type of the shape, e.g., "circle", "rectangle".
            size (tuple): 
                - If shape is Circle: It is a tuple (float,) and will be the radius of the ball as a proportion of window_x.
                - If shape is Rectangle: It is a tuple (float, float, ...) and will be side lengths as a proportion of window_x and window_y.
            shape_mass (float): Mass of the ball.
            shape_friction (float): Friction of the ball.
            shape_elasticity (float): Elasticity of the ball.
            default_position (tuple(float, float)): Proportion of window_x and window_y.
            default_velocity (tuple(float, float)): Initial velocity of the player.
            abilities (dict{str, str, ...}): Abilities of the player.
            health (int | str): Initial health of the player. Will be infinite health if it is a string.
            color (tuple(int, int, int)): Color of the player.

        Returns:
            Player: The created player object.
        """

        dynamic_body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)  # Ball body
        
        if shape_type == "circle":
            ball_radius = int(window_x * size[0])
            shape = Circle(
                shape_size=ball_radius,
                shape_mass=shape_mass,
                shape_friction=shape_friction,
                shape_elasticity=shape_elasticity,
                body=dynamic_body,
                collision_type=self.collision_type_player,
                is_draw_rotation_indicator=False,

                # **kwargs
                window_x=window_x,
                window_y=window_y,
                default_position=default_position,
                default_velocity=default_velocity
            )
        else:
            raise ValueError(f"Unsupported shape_type: {shape_type}. Currently, only 'circle' is supported.")

        player = Player(

            # **kwargs
            shape=shape,
            space=space,
            color=color,
            abilities=abilities,
            health=health
        )
        self.collision_type_player += 1
        # Store initial values for reset
        return player