import pygame
import os
import sys

# --- Configuration ---
# This script will build an absolute path to the 'assets' directory
# assuming the script is in '.../test/' and assets are in '.../assets/'
try:
    # Get the absolute path of the directory containing this script (e.g., .../test)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the project root and then into the 'assets' directory
    ASSETS_DIR = os.path.abspath(os.path.join(script_dir, '..', 'assets'))
except NameError:
    # Fallback for environments where __file__ is not defined (like some interactive shells)
    ASSETS_DIR = "assets"

BOUNCE_SOUND_FILE = "bounce.wav"
FALL_SOUND_FILE = "fall.wav"

# --- Pygame Initialization ---
print("Initializing Pygame...")
pygame.init()

# Create a small window to receive keyboard events
screen = pygame.display.set_mode((600, 250))
pygame.display.set_caption("Pygame Sound Test")
font = pygame.font.Font(None, 24)

# --- Sound Loading ---
sound_bounce = None
sound_fall = None
messages = []
print(f"Looking for assets in: {ASSETS_DIR}")
messages.append(f"Assets folder path: {ASSETS_DIR}")

try:
    # Initialize the sound mixer
    print("Initializing Pygame mixer...")
    pygame.mixer.init()
    if pygame.mixer.get_init():
        messages.append("Pygame mixer initialized successfully.")
        print("Mixer initialized.")
    else:
        messages.append("[ERROR] Failed to initialize Pygame mixer!")
        print("[ERROR] Failed to initialize Pygame mixer!")

    # Construct full paths to sound files
    bounce_path = os.path.join(ASSETS_DIR, BOUNCE_SOUND_FILE)
    fall_path = os.path.join(ASSETS_DIR, FALL_SOUND_FILE)

    # Load bounce sound
    messages.append(f"Attempting to load: {bounce_path}")
    if os.path.exists(bounce_path):
        sound_bounce = pygame.mixer.Sound(bounce_path)
        messages.append(f"-> SUCCESS: Loaded bounce.wav")
        print("-> SUCCESS: Loaded bounce.wav")
    else:
        messages.append(f"-> [ERROR] File not found: {bounce_path}")
        print(f"-> [ERROR] File not found: {bounce_path}")

    # Load fall sound
    messages.append(f"Attempting to load: {fall_path}")
    if os.path.exists(fall_path):
        sound_fall = pygame.mixer.Sound(fall_path)
        messages.append(f"-> SUCCESS: Loaded fall.wav")
        print("-> SUCCESS: Loaded fall.wav")
    else:
        messages.append(f"-> [ERROR] File not found: {fall_path}")
        print(f"-> [ERROR] File not found: {fall_path}")

except pygame.error as e:
    error_msg = f"A Pygame error occurred: {e}"
    messages.append(f"[FATAL] {error_msg}")
    print(f"[FATAL] {error_msg}")

# --- Main Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                if sound_bounce:
                    print("Playing bounce sound...")
                    sound_bounce.play()
                else:
                    print("Bounce sound is not loaded, cannot play.")
            elif event.key == pygame.K_f:
                if sound_fall:
                    print("Playing fall sound...")
                    sound_fall.play()
                else:
                    print("Fall sound is not loaded, cannot play.")
            elif event.key == pygame.K_q:
                running = False

    # --- Drawing information on screen ---
    screen.fill((41, 50, 65))  # Dark blue background
    
    instructions = [
        "Press 'B' to play Bounce sound",
        "Press 'F' to play Fall sound",
        "Press 'Q' or close the window to quit"
    ]
    
    # Display loading messages
    y_offset = 10
    for msg in messages:
        color = (255, 100, 100) if "[ERROR]" in msg or "[FATAL]" in msg else (100, 255, 100)
        text_surface = font.render(msg, True, color)
        screen.blit(text_surface, (10, y_offset))
        y_offset += 25
        
    y_offset += 5 # Separator line
    pygame.draw.line(screen, (100, 100, 100), (10, y_offset), (590, y_offset), 1)
    y_offset += 10

    # Display instructions
    for instruction in instructions:
        text_surface = font.render(instruction, True, (200, 200, 255))
        screen.blit(text_surface, (10, y_offset))
        y_offset += 25

    pygame.display.flip()

# --- Cleanup ---
print("Quitting Pygame.")
pygame.quit()
sys.exit()