import pymunk
import random
import time

from shapes.circle import Circle
from display import display_show_window, display_hide_window

# Constants
WINDOW_X = 1000
WINDOW_Y = 600
FPS = 120
BACKGROUND_COLOR = (255, 255, 255)  # white

# Initialize Pymunk physics
space = pymunk.Space()  # 创建一个pymunk物理空间
space.gravity = (0, 1000)  # 添加重力
space.damping = 0.9  # 空氣阻力, 物體每秒損失 1-space.damping 的速度

# Initialize bodies
dynamic_body = pymunk.Body()  # 動態身體, DYNAMIC 是預設的
kinematic_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
kinematic_body.position = (WINDOW_X / 2, 400)
kinematic_body.angular_velocity = 1  # 设置角速度（弧度/秒）
default_kinematic_position = kinematic_body.position
bodies = {
    "player_obj_body": dynamic_body, 
    "env_obj_body": kinematic_body, 
}

# Create ball
circle1 = Circle(
    position=(WINDOW_X / 2, 200),
    velocity=(0, 0),
    body=dynamic_body,
    shape_radio=10,
    shape_friction=100,
)

# Create platform
radio = 100
rotating_object = pymunk.Circle(kinematic_body, radio)
rotating_object.mass = 1  # 质量对 Kinematic 物体无意义，但需要避免除以零错误
rotating_object.friction = 0.7

# Add all objects to space
space.add(dynamic_body, kinematic_body, circle1.shape, rotating_object)

def reset_game():
    """Reset the game state to initial conditions with random rotation"""
    circle1.reset()
    kinematic_body.position = default_kinematic_position
    rotate_speed = random.randrange(-1, 2, 2)
    kinematic_body.angular_velocity = rotate_speed

    return time.time()

if __name__ == "__main__":
    # display_show_window(
    #     window_size=(WINDOW_X, WINDOW_Y), 
    #     space=space, 
    #     bodies=bodies, 
    #     reset_game=reset_game, 
    #     bg_color=BACKGROUND_COLOR, 
    # )

    display_hide_window(
        window_size=(WINDOW_X, WINDOW_Y), 
        space=space, 
        bodies=bodies, 
        reset_game=reset_game, 
        bg_color=BACKGROUND_COLOR, 
    )


