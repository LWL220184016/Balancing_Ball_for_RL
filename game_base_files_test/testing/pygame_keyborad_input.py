import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Character Control Example")

# Set up colors
black = (0, 0, 0)
white = (255, 255, 255)

# Character settings
character_pos = [400, 300]
character_speed = 5
character_size = 50

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Get the state of all keys
    keys = pygame.key.get_pressed()

    # Control character movement
    if keys[pygame.K_LEFT]:
        character_pos[0] -= character_speed
    if keys[pygame.K_RIGHT]:
        character_pos[0] += character_speed
    if keys[pygame.K_UP]:
        character_pos[1] -= character_speed
    if keys[pygame.K_DOWN]:
        character_pos[1] += character_speed

    # Fill the screen with black
    screen.fill(black)
    
    # Draw the character (a simple rectangle)
    pygame.draw.rect(screen, white, (character_pos[0], character_pos[1], character_size, character_size))

    # Update the display
    pygame.display.flip()

    # Frame rate
    pygame.time.Clock().tick(60)