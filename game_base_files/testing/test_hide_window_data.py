import pygame
import numpy as np

# 初始化 Pygame
pygame.init()

# 设置画面尺寸
width, height = 640, 480
screen = pygame.Surface((width, height))  # 创建隐藏的表面
# screen = pygame.display.set_mode((width, height))

# 游戏主循环
running = True
frame_count = 0  # 帧计数

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 在此添加游戏逻辑和绘制代码，例如绘制一个白色矩形
    pygame.draw.rect(screen, (255, 255, 255), (width // 4, height // 4, width // 2, height // 2))

    # 获取画面数据
    screen_data = pygame.surfarray.array3d(screen)  # 获取数据
    screen_data = np.transpose(screen_data, (1, 0, 2))  # 转置以符合 (height, width, channels)

    # 将 NumPy 数组转换为 Pygame Surface
    surface = pygame.surfarray.make_surface(screen_data)

    # 保存为图片
    if frame_count % 10 == 0:  # 每10帧保存一次
        pygame.image.save(surface, f"frame_{frame_count}.png")
        
    frame_count += 1

pygame.quit()