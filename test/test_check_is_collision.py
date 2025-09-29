import pymunk
import pymunk.pygame_util
import pygame

def post_solve_collision_handler(arbiter, space, data):
    """
    這個函數在碰撞解決後被調用。
    它會印出關於碰撞的資訊。
    """
    print(f"Collision between shapes with collision_type: {arbiter.shapes[0].collision_type} and {arbiter.shapes[1].collision_type}")
    print(f"Total impulse applied: {arbiter.total_impulse}")
    print(f"Is this the first contact: {arbiter.is_first_contact}")
    
    # 印出接觸點資訊
    if arbiter.contact_point_set:
        print(f"Number of contact points: {len(arbiter.contact_point_set.points)}")
        for point in arbiter.contact_point_set.points:
            print(f" - Contact Point A (on 1st shape): {point.point_a.x:.2f}, {point.point_a.y:.2f}")
            print(f" - Contact Point B (on 2nd shape): {point.point_b.x:.2f}, {point.point_b.y:.2f}")
            print(f" - Penetration Distance: {point.distance:.2f}")
    print("-" * 30)
    return True

def main():
    # Pygame 初始化
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Pymunk Collision Simulation")
    clock = pygame.time.Clock()
    
    # 1. 初始化 Pymunk 空間
    space = pymunk.Space()
    space.gravity = (0, -981)  # Y軸向下的重力

    # Pymunk 繪圖選項
    draw_options = pymunk.pygame_util.DrawOptions(screen)

    # 2. 創建靜態地板
    static_body = space.static_body
    floor = pymunk.Segment(static_body, (-50, 5), (50, 5), 1)
    floor.friction = 0.8
    floor.collision_type = 1 # 為地板設置碰撞類型
    space.add(floor)

    # 3. 創建一個動態的球
    mass = 1
    radius = 5
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = (0, 20) # 設置球的初始位置
    shape = pymunk.Circle(body, radius)
    shape.friction = 0.7
    shape.collision_type = 2 # 為球設置碰撞類型
    space.add(body, shape)

    # 4. 設置碰撞處理器
    # 使用 on_collision(None, None, ...) 來設置一個萬用字元(預設)處理器。
    # 這會捕捉所有未被更具體處理器處理的碰撞，非常方便。
    # 我們使用 post_solve 回調，因為它在碰撞被物理引擎處理後觸發，可以獲取衝量等資訊。
    space.on_collision(None, None, post_solve=post_solve_collision_handler)

    # 5. 運行模擬
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # 清除螢幕
        screen.fill((255, 255, 255)) # 白色背景

        # 繪製 Pymunk 空間
        space.debug_draw(draw_options)

        # 更新物理模擬
        space.step(1 / 60.0)

        # 更新螢幕
        pygame.display.flip()

        # 控制幀率
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
