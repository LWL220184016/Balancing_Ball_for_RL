import pymunk
import pygame as pg
import sys

from pymunk.pygame_util import DrawOptions

WINDOW_X = 1000
WINDOW_Y = 600

# 创建空间并设置重力
space = pymunk.Space()
space.gravity = (0, 1000)  # 重力向下（例如 1000 像素/秒²）

# 创建 Kinematic 类型的物体（不受重力影响）
kinematic_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
kinematic_body.position = (400, 300)  # 固定在屏幕中央
kinematic_body.angular_velocity = 3  # 设置角速度（弧度/秒）

# 创建矩形形状并附加到物体
width, height = 100, 50
rectangle = pymunk.Poly.create_box(kinematic_body, (width, height))
rectangle.mass = 1  # 质量对 Kinematic 物体无意义，但需要避免除以零错误
rectangle.friction = 0.7

# 将物体和形状添加到空间
space.add(kinematic_body, rectangle)

# 模拟循环

if __name__ == "__main__":
    screen = pg.display.set_mode((WINDOW_X, WINDOW_Y))
    draw_options = DrawOptions(screen)
    background_color = (255, 255, 255) # white
    fps = 120 # frame per second
    clock = pg.time.Clock()

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

        keys = pg.key.get_pressed()

        # if keys[pg.K_UP]:
        #     character_pos[1] -= character_speed
        # if keys[pg.K_DOWN]:
        #     character_pos[1] += character_speed

        s = "FPS: {}".format(clock.get_fps())
        pg.display.set_caption(s)
        screen.fill(background_color)

        space.debug_draw(draw_options)
        space.step(1 / fps)

        pg.display.flip()
        clock.tick(fps)