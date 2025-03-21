import pymunk
import pygame
import sys

from shapes.circle import Circle
from pymunk.pygame_util import DrawOptions

WINDOW_X = 1000
WINDOW_Y = 600

space = pymunk.Space() # 创建一个pymunk物理空间
space.gravity = (0, 1000) # 添加重力
space.damping = 0.9 # 空氣阻力, 物體每秒損失 1-space.damping 的速度

dynamic_body = pymunk.Body() # 動態身體, DYNAMIC 是預設的
kinematic_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
kinematic_body.position = (WINDOW_X / 2, 400)
kinematic_body.angular_velocity = 1  # 设置角速度（弧度/秒）

circle1 = Circle(
    position = (WINDOW_X / 2, 200), 
    velocity = (0, 0), 
    body = dynamic_body, 
    shape_radio = 10, 
    shape_friction = 100, 
)

width, height, radio= 100, 100, 100
# rotating_object = pymunk.Poly.create_box(kinematic_body, (width, height))
rotating_object = pymunk.Circle(kinematic_body, radio)
rotating_object.mass = 1  # 质量对 Kinematic 物体无意义，但需要避免除以零错误
rotating_object.friction = 0.7

space.add(dynamic_body, kinematic_body, circle1.shape, rotating_object) # 将身体和形状加入 pymunk 空间

if __name__ == "__main__":
    import random
    import time
    from record import Recorder
    
    recorder = Recorder("game_history_record")
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_X, WINDOW_Y))
    draw_options = DrawOptions(screen)
    background_color = (255, 255, 255) # white
    fps = 120 # frame per second
    clock = pygame.time.Clock()

    game_duration = time.time()
    while True:
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
            circle1.reset()

        # if keys[pygame.K_UP]:
        #     character_pos[1] -= character_speed
        # if keys[pygame.K_DOWN]:
        #     character_pos[1] += character_speed

        if dynamic_body.position[1] > 600:
            game_total_duration = time.time() - game_duration
            game_duration = time.time()
            dynamic_body.angular_velocity = 0
            circle1.reset()
            recorder.add_no_limit(game_total_duration)

            rotate_speed = random.randrange(-1, 2, 2)
            kinematic_body.angular_velocity = rotate_speed


        s = "FPS: {}".format(clock.get_fps())
        pygame.display.set_caption(s)
        screen.fill(background_color)
        space.debug_draw(draw_options)
        
        font = pygame.font.Font(None, 30)
        text1 = f"""Ball speed: {format(dynamic_body.angular_velocity, ".2f")}
Ball position: {format(dynamic_body.position[0], ".2f")}, {format(dynamic_body.position[1], ".2f")}
"""
        y = 5
        for line in text1.splitlines():
            text1 = font.render(line, True, pygame.Color("black"))
            screen.blit(text1, (5, y))
            y += 25

        text2 = f"{format(time.time() - game_duration, '.2f')}"
        y = 5
        text2 = font.render(text2, True, pygame.Color("red"))
        screen.blit(text2, (WINDOW_X - 50, y))

        space.step(1 / fps)

        pygame.display.flip()
        clock.tick(fps)


