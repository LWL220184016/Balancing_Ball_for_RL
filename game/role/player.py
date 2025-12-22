import pymunk

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
        self.last_direction = None  # 用於追踪玩家上一次移動的方向
        self.direction_count = 0  # 用於追踪玩家是否一直向同一方向移動
        self.reward_per_step = 0  # 每一步的獎勵

        # 用於記錄狀態比如是否已經受到在重置前只能受到一次的懲罰
        self.special_status = {}  # 特殊狀態

    def get_state(self, window_size: tuple, velocity_scale: float = 200.0, **kwargs):
        """
        獲取正規化狀態。
        使用 tanh 函數來處理沒有固定上限的速度。
        velocity_scale: 用於調整速度的靈敏度。
        """
        # 首先，從父類獲取基本狀態（位置、技能冷卻等）
        state = super().get_state(window_size=window_size, velocity_scale=velocity_scale, **kwargs)

        return state

    def reset(self, **kwargs):
        """Reset the player when dropped."""

        super().reset(**kwargs)
        self.is_alive = True
        self.is_on_ground = False
        self.special_status = {}

    def reset_episodes(self, **kwargs):
        """Reset the player at the start of each episode."""

        self.reset(**kwargs)

        self.set_last_direction(None)
        self.set_direction_count(0)

    def apply_force_at_world_point(self, force: pymunk.Vec2d, point: tuple[float, float]):
        self.shape.apply_force_at_world_point(force, point)

    def get_reward_per_step(self):
        return self.reward_per_step
    
    def get_last_direction(self):
        return self.last_direction

    def get_direction_count(self):
        return self.direction_count
    
    def get_special_status(self, status_key: str):
        return self.special_status.get(status_key, False)
    
    def set_reward_per_step(self, reward: float):
        self.reward_per_step = reward
    
    def add_reward_per_step(self, reward: float):
        self.reward_per_step += reward

    def set_last_direction(self, direction: str):
        self.last_direction = direction

    def set_direction_count(self, count: int):
        self.direction_count = count

    def set_special_status(self, status_key: str, status_value):
        self.special_status[status_key] = status_value

    def add_direction_count(self, count: int):
        self.direction_count += count

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
                      default_angular_velocity: float = None,
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
                default_velocity=default_velocity,
                default_angular_velocity=default_angular_velocity,
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