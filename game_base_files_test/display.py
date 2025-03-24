import pygame
import sys
import time

from pymunk.pygame_util import DrawOptions
from record import Recorder
    
def display_show_window(
            window_size = (1000, 600), 
            space = None, 
            bodies: dict = None, 
            FPS = 120, 
            reset_game = None, 
            bg_color: tuple = (255, 255, 255),  # white

        ):
    """
    this function will show the game window, for test the model
    """
    
    # Initialize pygame and recorder
    pygame.init()
    recorder = Recorder("game_history_record")
    screen = pygame.display.set_mode(window_size)
    draw_options = DrawOptions(screen)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 30)
    game_duration = time.time()
    dynamic_body = bodies.get("player_obj_body", None)
    kinematic_body = bodies.get("env_obj_body", None)
    
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
        if dynamic_body.position[1] > window_size[1]:
            game_total_duration = time.time() - game_duration
            recorder.add_no_limit(game_total_duration)
            game_duration = reset_game()

        # Update display
        pygame.display.set_caption(f"FPS: {clock.get_fps():.1f}")
        screen.fill(bg_color)
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
        screen.blit(rendered_timer, (window_size[0] - 100, 5))

        # Update physics
        space.step(1 / FPS)

        # Refresh display
        pygame.display.flip()
        clock.tick(FPS)


def display_hide_window(
            window_size = (1000, 600), 
            space = None, 
            bodies: dict = None, 
            FPS = 120, 
            reset_game = None, 
            bg_color: tuple = (255, 255, 255),  # white

        ):
    """
    this function will hide the game window, for training the model in server
    """
    import os
    
    # Initialize pygame and recorder
    pygame.init()
    recorder = Recorder("game_history_record")
    screen = pygame.Surface(window_size)  # 创建隐藏的表面
    draw_options = DrawOptions(screen)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 30)
    game_duration = time.time()
    dynamic_body = bodies.get("player_obj_body", None)
    kinematic_body = bodies.get("env_obj_body", None)

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.dirname(CURRENT_DIR + "/capture/"), exist_ok=True)
    
    frame_count = 0
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
        if dynamic_body.position[1] > window_size[1]:
            game_total_duration = time.time() - game_duration
            recorder.add_no_limit(game_total_duration)
            game_duration = reset_game()

        # Update display
        pygame.display.set_caption(f"FPS: {clock.get_fps():.1f}")
        screen.fill(bg_color)
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
        screen.blit(rendered_timer, (window_size[0] - 100, 5))

        if keys[pygame.K_p]:
            timer_text = "Holding button p"
            rendered_timer = font.render(timer_text, True, pygame.Color("purple"))
            screen.blit(rendered_timer, (window_size[0]/2, 5))
        timer_text = "Holding button dwde"
        rendered_timer = font.render(timer_text, True, pygame.Color("purple"))
        screen.blit(rendered_timer, (window_size[0]/2, 50))
        # Update physics
        space.step(1 / FPS)

        # Refresh display
        clock.tick(FPS)

        screen_data = pygame.surfarray.array3d(screen)  # 获取数据
        # screen_data = np.transpose(screen_data, (1, 0, 2))  # 转置以符合 (height, width, channels)

        # 将 NumPy 数组转换为 Pygame Surface
        surface = pygame.surfarray.make_surface(screen_data)
        
        # 保存为图片
        if frame_count % 60 == 0:  # 每10帧保存一次
            pygame.image.save(surface, f"capture/frame_{frame_count/60}.png")
            
        frame_count += 1