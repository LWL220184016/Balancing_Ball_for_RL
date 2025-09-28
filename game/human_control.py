
import pygame

try:
    from balancing_ball_game import BalancingBallGame
except ImportError:
    from game.balancing_ball_game import BalancingBallGame


class HumanControl:
    
    def __init__(self, game: BalancingBallGame):
        self.game = game

    def get_player_actions(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game.get_game_over():
                    self.game.reset()

        # Process keyboard controls for continuous actions
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        actions = []

        # Player 1 controls (WASD + Space for jump)
        p1_x_force = 0
        p1_y_force = 0
        p1_ability1 = None
        if keys[pygame.K_a]:
            p1_x_force = -1  # Full left force
        elif keys[pygame.K_d]:
            p1_x_force = 1  # Full right force

        if keys[pygame.K_SPACE]:
            p1_y_force = 1  # Jump force persentage (0 to 1)

        if mouse_buttons[0]:
            p1_ability1 = pygame.mouse.get_pos()  # Activate ability 1

        actions.append((p1_x_force, p1_y_force, p1_ability1))

        if self.game.get_num_players() > 1:
            # Player 2 controls (Arrow keys + Right Ctrl for jump)
            p2_x_force = 0
            p2_y_force = 0
            p2_ability1 = None
            if keys[pygame.K_LEFT]:
                p2_x_force = -1  # Full left force
            elif keys[pygame.K_RIGHT]:
                p2_x_force = 1  # Full right force

            if keys[pygame.K_RCTRL]:
                p2_y_force = 1  # Jump force persentage (0 to 1)

            if mouse_buttons[2]:
                p2_ability1 = pygame.mouse.get_pos()  # Activate ability 1

            actions.append((p2_x_force, p2_y_force, p2_ability1))        

        return actions