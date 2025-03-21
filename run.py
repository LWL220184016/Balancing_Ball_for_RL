import pymunk
import pygame
import sys
import random
import time

from shapes.circle import Circle
from pymunk.pygame_util import DrawOptions

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
    from record import Recorder
    
    # Initialize pygame and recorder
    pygame.init()
    recorder = Recorder("game_history_record")
    screen = pygame.display.set_mode((WINDOW_X, WINDOW_Y))
    draw_options = DrawOptions(screen)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 30)

    game_duration = time.time()
    
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()

        # Control character movement
        if keys[pygame.K_LEFT]:
            dynamic_body.angular_velocity -= 1
        if keys[pygame.K_RIGHT]:
            dynamic_body.angular_velocity += 1
        if keys[pygame.K_r]:
            game_duration = reset_game()

        # Check if ball falls off screen
        if dynamic_body.position[1] > WINDOW_Y:
            game_total_duration = time.time() - game_duration
            recorder.add_no_limit(game_total_duration)
            game_duration = reset_game()

        # Update display
        pygame.display.set_caption(f"FPS: {clock.get_fps():.1f}")
        screen.fill(BACKGROUND_COLOR)
        space.debug_draw(draw_options)
        
        # Display information
        text1 = f"""Ball speed: {dynamic_body.angular_velocity:.2f}
Ball position: {dynamic_body.position[0]:.2f}, {dynamic_body.position[1]:.2f}
Platform rotation: {kinematic_body.angular_velocity:.2f}"""
        
        y = 5
        for line in text1.splitlines():
            rendered_text = font.render(line, True, pygame.Color("black"))
            screen.blit(rendered_text, (5, y))
            y += 25

        # Display timer
        timer_text = f"{time.time() - game_duration:.2f}"
        rendered_timer = font.render(timer_text, True, pygame.Color("red"))
        screen.blit(rendered_timer, (WINDOW_X - 100, 5))

        # Update physics
        space.step(1 / FPS)

        # Refresh display
        pygame.display.flip()
        clock.tick(FPS)


