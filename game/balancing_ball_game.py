import pymunk
import pygame
import time
import os
import base64
import numpy as np
# import IPython.display as ipd

from typing import Dict, Tuple, Optional
# from IPython.display import display, Image, clear_output
from io import BytesIO

try:
    from record import Recorder
except ImportError:
    from game.record import Recorder

try:
    from levels.levels import get_level
except ImportError:
    from game.levels.levels import get_level


class BalancingBallGame:
    """
    A physics-based balancing ball game that can run standalone or be used as a Gym environment.
    """

    # Game constants

    # Visual settings for indie style
    BACKGROUND_COLOR = (41, 50, 65)  # Dark blue background
    PLATFORM_COLOR = (235, 64, 52)  # Red platform

    def __init__(self,
                 render_mode: str = "human",
                 sound_enabled: bool = True,
                 window_x: int = 1000,
                 window_y: int = 600,
                 max_step: int = 30000,
                 player_configs: dict = None,
                 platform_configs: dict = None,
                 environment_configs: dict = None,
                 reward_staying_alive: float = 0.1,
                 penalty_falling: float = -10.0,
                 level: int = None,
                 fps: int = 120,
                 capture_per_second: int = None,
                 speed_reward_multiplier: float = 0.01,  # Reward for maintaining speed
                 opponent_fall_bonus: float = 15.0,  # Bonus for causing opponent to fall
                 survival_bonus: float = 0.5,  # Bonus for staying alive when opponent falls
                ):
        """
        Initialize the balancing ball game.

        Args:
            render_mode: "human" for visible window, "rgb_array" for gym env, "headless" for no rendering
            sound_enabled: Whether to enable sound effects
            max_step: 1 step = 1/fps, if fps = 120, 1 step = 1/120
            reward_staying_alive: float = 0.1,
            penalty_falling: float = -10.0,
            fps: frame per second
            capture_per_second: save game screen as a image every second, None means no capture
            speed_reward_multiplier: Multiplier for speed-based rewards
        """
        # Game parameters
        self.max_step = max_step
        self.reward_staying_alive = reward_staying_alive
        self.penalty_falling = penalty_falling
        self.fps = fps
        self.window_x = window_x
        self.window_y = window_y
        self.speed_reward_multiplier = speed_reward_multiplier
        self.opponent_fall_bonus = opponent_fall_bonus
        self.survival_bonus = survival_bonus

        self.recorder = Recorder("game_history_record")
        self.render_mode = render_mode
        self.sound_enabled = sound_enabled

        # Initialize physics space
        self.space = pymunk.Space()

        self.level = get_level(level, self.space, player_configs, platform_configs, environment_configs)
        self.players, self.platforms = self.level.setup(self.window_x, self.window_y)
        self.kinematic_body_platforms = []

        for platform in self.platforms:
            self.kinematic_body_platforms.append(platform["body"])

        self.platform_length = self.platforms[0]["platform_length"]
        self.num_players = len(self.players)

        # Game state tracking
        self.steps = 0
        self.start_time = time.time()
        self.game_over = False
        self.score = [0] * self.num_players  # Score for each player
        self.winner = None
        self.last_speeds = [0] * self.num_players  # Track last speed for each player
        self.players_fell_this_step = [False] * self.num_players  # Track who fell this step

        # Initialize Pygame if needed
        if self.render_mode in ["human", "rgb_array", "rgb_array_and_human", "rgb_array_and_human_in_colab"]:
            self._setup_pygame()
        else:
            print("render_mode is not human or rgb_array, so no pygame setup.")

        self.capture_per_second = capture_per_second

        # Create folders for captures if needed
        # CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        CURRENT_DIR = "."
        os.makedirs(os.path.dirname(CURRENT_DIR + "/capture/"), exist_ok=True)


    def _setup_pygame(self):
        """Set up PyGame for rendering"""
        pygame.init()
        self.frame_count = 0

        if self.sound_enabled:
            self._load_sounds()

        if self.render_mode == "human":
            self.screen = pygame.display.set_mode((self.window_x, self.window_y))
            pygame.display.set_caption("Balancing Ball - Indie Game")
            self.font = pygame.font.Font(None, int(self.window_x / 34))

        elif self.render_mode == "rgb_array":
            self.screen = pygame.Surface((self.window_x, self.window_y))

        elif self.render_mode == "rgb_array_and_human": # todo
            print("rgb_array_and_human mode is not supported yet.")

        elif self.render_mode == "rgb_array_and_human_in_colab": # todo
            import IPython.display as ipd
            from pymunk.pygame_util import DrawOptions

            self.screen = pygame.Surface((self.window_x, self.window_y))  # Create hidden surface

            # Set up display in Colab
            self.draw_options = DrawOptions(self.screen)
            html_display = ipd.HTML('''
                <div id="pygame-output" style="width:100%;">
                    <img id="pygame-img" style="width:100%;">
                </div>
            ''')
            self.display_handle = ipd.display(html_display, display_id='pygame_display')

            self.last_update_time = time.time()
            self.update_interval = 1.0 / 15  # Update display at 15 FPS to avoid overwhelming Colab
            self.font = pygame.font.Font(None, int(self.window_x / 34))


        else:
            print("Invalid render mode. Using headless mode.")

        self.clock = pygame.time.Clock()

        # Create custom draw options for indie style

    def _load_sounds(self):
        """Load game sound effects"""
        try:
            pygame.mixer.init()
            self.sound_bounce = pygame.mixer.Sound("assets/bounce.wav") if os.path.exists("assets/bounce.wav") else None
            self.sound_fall = pygame.mixer.Sound("assets/fall.wav") if os.path.exists("assets/fall.wav") else None
        except Exception:
            print("Sound loading error")
            self.sound_enabled = False
            pass

    def reset(self) -> np.ndarray:
        """Reset the game state and return the initial observation"""
        # Reset physics objects
        self.level.reset()

        # Reset game state
        self.steps = 0
        self.start_time = time.time()
        self.game_over = False
        self.score = [0] * self.num_players
        self.winner = None
        self.last_speeds = [0] * self.num_players
        self.players_fell_this_step = [False] * self.num_players

        # Return initial observation
        return self._get_observation()

    def step(self, pactions: list = [Tuple[float, float]]) -> Tuple[np.ndarray, list, bool, Dict]:
        """
        Take a step in the game using the given actions.

        Args:
            actions: List of continuous actions [-1.0, 1.0] for each player controlling horizontal force

        Returns:
            observation: Game state observation
            rewards: List of rewards for each player
            terminated: Whether episode is done
            info: Additional information
        """
        self.players_fell_this_step = [False] * self.num_players
        
        # 需要保留直到移除舊模型，詳情看函數說明
        # actions = pactions if isinstance(pactions, list) else [pactions]
        # actions = self.calculate_player_speed_old(actions)

        for i, player in enumerate(self.players):
            player.perform_action(pactions[i])
        self.level.action()

        # Step the physics simulation
        self.space.step(1/self.fps)

        # Check game state
        self.steps += 1
        rewards, terminated = self.reward()
        self.step_rewards = rewards

        return self._get_observation(), rewards, terminated

    def reward(self):
        """
        Calculate and return the reward for the current state.
        """
        rewards = [0] * self.num_players

        # Check if balls fall off screen and calculate rewards
        alive_count = 0
        
        for i, player in enumerate(self.players):
            if not player.is_alive:
                continue

            ball_x, ball_y = player.get_position()

            # Check if player falls
            if (ball_y > self.window_y or
                ball_x < 0 or ball_x > self.window_x):

                player.is_alive = False
                self.players_fell_this_step[i] = True
                rewards[i] = self.penalty_falling

                if self.sound_enabled and self.sound_fall:
                    self.sound_fall.play()
            else:
                alive_count += 1
                
                # 基礎生存獎勵
                survival_reward = self.reward_staying_alive

                # 速度獎勵 - 鼓勵保持移動
                vx, vy = player.get_velocity()
                current_speed = abs(vx) + abs(vy)
                speed_reward = min(current_speed * self.speed_reward_multiplier, 0.1)  # 限制最大速度獎勵

                # 不同關卡的特別獎勵
                level_reward = self.level.reward(ball_x)

                rewards[i] = survival_reward + speed_reward + level_reward
                self.last_speeds[i] = current_speed

        # 處理對手掉落的獎勵
        for i, player in enumerate(self.players):
            if player.is_alive:  # 如果這個玩家還活著
                # 檢查是否有對手在這步掉落
                opponents_fell = any(self.players_fell_this_step[j] for j in range(self.num_players) if j != i)
                if opponents_fell:
                    rewards[i] += self.opponent_fall_bonus  # 獲得擊敗對手的獎勵
                    print(f"Player {i+1} gets opponent fall bonus: {self.opponent_fall_bonus}")

            self.score[i] += rewards[i]

        # Check if game should end
        terminated = False
        if alive_count <= 1 or self.steps >= self.max_step:
            print("Final Scores: ", self.score)
            terminated = True
            self.game_over = True

            # Determine winner (last player alive or highest score)
            if alive_count == 1:
                self.winner = next(i for i in range(self.num_players) if self.players[i].is_alive)
                # Give bonus to winner
                rewards[self.winner] += self.survival_bonus * self.steps / 100  # 生存時間越長獎勵越多
                self.score[self.winner] += rewards[self.winner]
                print(f"Winner: Player {self.winner + 1}")
            elif alive_count == 0:
                self.winner = None  # Draw
                print("Draw - all players fell")
            else:
                # Game ended due to max steps, winner is highest score
                self.winner = np.argmax(self.score)
                print(f"Time limit reached. Winner by score: Player {self.winner + 1}")

            result = {
                "game_total_duration": f"{time.time() - self.start_time:.2f}",
                "scores": self.score,
                "winner": self.winner,
                "steps": self.steps
            }
            self.recorder.add_no_limit(result)

        return rewards, terminated

    def _get_observation(self) -> np.ndarray:
        """Convert game state to observation for RL agent"""
        # update particles and draw them
        screen_data = self.render() # 获取数据

        if self.capture_per_second is not None and self.frame_count % self.capture_per_second == 0:  # Every second at 60 FPS
            pygame.image.save(self.screen, f"capture/frame_{self.frame_count/60}.png")

        self.frame_count += 1
        return screen_data

    def render(self) -> Optional[np.ndarray]:
        """Render the current game state"""
        if self.render_mode == "headless":
            return None

        # Clear screen with background color
        self.screen.fill(self.BACKGROUND_COLOR)

        # Custom drawing (for indie style)
        self._draw_indie_style()


        # Update display if in human mode
        if self.render_mode == "human":
            # Draw game information
            self._draw_game_info()
            pygame.display.flip()
            self.clock.tick(self.fps)
            return None

        elif self.render_mode == "rgb_array":
            # Return RGB array for gym environment
            return pygame.surfarray.array3d(self.screen)

        elif self.render_mode == "rgb_array_and_human": # todo
            print("rgb_array_and_human mode is not supported yet.")

        elif self.render_mode == "rgb_array_and_human_in_colab":
            self.space.debug_draw(self.draw_options)
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                # Convert Pygame surface to an image that can be displayed in Colab
                buffer = BytesIO()
                pygame.image.save(self.screen, buffer, 'PNG')
                buffer.seek(0)
                img_data = base64.b64encode(buffer.read()).decode('utf-8')

                # Update the HTML image
                self.display_handle.update(ipd.HTML(f'''
                    <div id="pygame-output" style="width:100%;">
                        <img id="pygame-img" src="data:image/png;base64,{img_data}" style="width:100%;">
                    </div>
                '''))

                self.last_update_time = current_time
            return pygame.surfarray.array3d(self.screen)
        else:
            pass

    def _draw_indie_style(self):
        """Draw game objects with indie game aesthetic"""
        # Draw players
        for player in self.players:
            if player.is_alive:
                player._draw_indie_style(self.screen)

        # Draw platforms by checking the shape type associated with each body
        for platform_body in self.kinematic_body_platforms:
            # A body can have multiple shapes, iterate through them
            for shape in platform_body.shapes:
                if isinstance(shape, pymunk.Poly):
                    # It's a polygon, draw it
                    platform_points = [v.rotated(platform_body.angle) + platform_body.position for v in shape.get_vertices()]
                    
                    pygame.draw.polygon(self.screen, self.PLATFORM_COLOR, platform_points)
                    pygame.draw.polygon(self.screen, (255, 255, 255), platform_points, 2)
                    
                    # For rotation indicator, we need a position and a "radius"
                    # We can approximate the radius from the shape's bounding box
                    radius_approx = (shape.bb.right - shape.bb.left) / 2
                    self._draw_rotation_indicator(platform_body.position, radius_approx, platform_body.angular_velocity, platform_body)

                elif isinstance(shape, pymunk.Circle):
                    # It's a circle, draw it
                    platform_pos = (int(platform_body.position.x), int(platform_body.position.y))
                    radius = int(shape.radius)
                    
                    pygame.draw.circle(self.screen, self.PLATFORM_COLOR, platform_pos, radius)
                    pygame.draw.circle(self.screen, (255, 255, 255), platform_pos, radius, 2)
                    
                    self._draw_rotation_indicator(platform_pos, radius, platform_body.angular_velocity, platform_body)

    def _draw_rotation_indicator(self, position, radius, angular_velocity, body):
        """Draw an indicator showing the platform's rotation direction and speed"""
        # Only draw the indicator if there's some rotation
        if abs(angular_velocity) < 0.1:
            return

        # Calculate indicator properties based on angular velocity
        indicator_color = (50, 255, 150) if angular_velocity > 0 else (255, 150, 50)
        num_arrows = min(3, max(1, int(abs(angular_velocity))))
        indicator_radius = radius - 20  # Place indicator inside the platform

        # Draw arrow indicators along the platform's circumference
        start_angle = body.angle

        for i in range(num_arrows):
            # Calculate arrow position
            arrow_angle = start_angle + i * (2 * np.pi / num_arrows)

            # Calculate arrow start and end points
            base_x = position[0] + int(np.cos(arrow_angle) * indicator_radius)
            base_y = position[1] + int(np.sin(arrow_angle) * indicator_radius)

            # Determine arrow direction based on angular velocity
            if angular_velocity > 0:  # Clockwise
                arrow_end_angle = arrow_angle + 0.3
            else:  # Counter-clockwise
                arrow_end_angle = arrow_angle - 0.3

            tip_x = position[0] + int(np.cos(arrow_end_angle) * (indicator_radius + 15))
            tip_y = position[1] + int(np.sin(arrow_end_angle) * (indicator_radius + 15))

            # Draw arrow line
            pygame.draw.line(self.screen, indicator_color, (base_x, base_y), (tip_x, tip_y), 3)

            # Draw arrowhead
            arrowhead_size = 7
            pygame.draw.circle(self.screen, indicator_color, (tip_x, tip_y), arrowhead_size)

    def _draw_game_info(self):
        """Draw game information on screen"""
        # Create texts
        time_text = f"Time: {time.time() - self.start_time:.1f}"
        score_texts = [f"P{i+1}: {self.score[i]:.1f} + {self.step_rewards[i]:.1f}" for i in range(self.num_players)]

        # Render texts
        time_surface = self.font.render(time_text, True, (255, 255, 255))
        score_surfaces = [self.font.render(text, True, (255, 255, 255)) for text in score_texts]

        # Draw text backgrounds and texts
        pygame.draw.rect(self.screen, (0, 0, 0, 128),
                        (5, 5, time_surface.get_width() + 10, time_surface.get_height() + 5))
        self.screen.blit(time_surface, (10, 10))

        # Draw scores
        y_offset = 40
        for i, surface in enumerate(score_surfaces):
            color = self.players[i].get_color() if self.players[i].is_alive else (100, 100, 100)
            pygame.draw.rect(self.screen, (0, 0, 0, 128),
                            (5, y_offset, surface.get_width() + 10, surface.get_height() + 5))
            colored_surface = self.font.render(score_texts[i], True, color)
            self.screen.blit(colored_surface, (10, y_offset))
            y_offset += 30

        # Draw game over screen
        if self.game_over:
            if self.winner is not None:
                game_over_text = f"WINNER: Player {self.winner + 1} - Press R to restart"
            else:
                game_over_text = "DRAW - Press R to restart"
            game_over_surface = self.font.render(game_over_text, True, (255, 255, 255))

            # Draw semi-transparent background
            overlay = pygame.Surface((self.window_x, self.window_y), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))

            # Draw text
            self.screen.blit(game_over_surface,
                           (self.window_x/2 - game_over_surface.get_width()/2,
                            self.window_y/2 - game_over_surface.get_height()/2))

    def close(self):
        """Close the game and clean up resources"""
        if self.render_mode in ["human", "rgb_array"]:
            pygame.quit()
            
    def calculate_player_speed_old(self, moving_direction: list = []):
        """
        Calculate the speed of the player ball

        新訓練的模型是連續動作空間，範圍包含正數和負數，
        但是早期訓練的模型只能輸出 0 和 1，分別代表向左和向右，因此有必要保留這個函數直到移除舊模型
        """
        # In order to fit the model action space, the model can currently only output 0 and 1, so 2 is no action

        for i in range(len(moving_direction)):
            if moving_direction[i] == 0:
                moving_direction[i] = pymunk.Vec2d(self.players[i].get_speed() * -1, 0)

            elif moving_direction[i] == 1:
                moving_direction[i] = pymunk.Vec2d(self.players[i].get_speed(), 0)

            elif moving_direction[i] == 2:
                moving_direction[i] = pymunk.Vec2d(0, 0)

            else:
                raise ValueError(f"Invalid action: {moving_direction}. Action must be 0 (left), 1 (right), or 2 (no action).")
            
            # 遍歷所有玩家
        for i, player in enumerate(self.players):
            # 如果 actions 列表不夠長，則對後續玩家使用 0 作為預設動作
            force_vector = moving_direction[i]
            player.move(force_vector)

    def run_standalone(self):
        """Run the game in standalone mode with keyboard controls"""
        if self.render_mode not in ["human", "rgb_array_and_human_in_colab"]:
            raise ValueError("Standalone mode requires render_mode='human' or 'rgb_array_and_human_in_colab'")

        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        self.reset()

            # Process keyboard controls for continuous actions
            keys = pygame.key.get_pressed()
            actions = []

            # Player 1 controls (WASD + Space for jump)
            p1_x_force = 0
            p1_y_force = 0
            if keys[pygame.K_a]:
                p1_x_force = -1  # Full left force
            elif keys[pygame.K_d]:
                p1_x_force = 1  # Full right force

            if keys[pygame.K_SPACE]:
                p1_y_force = 1  # Jump force persentage (0 to 1)

            actions.append((p1_x_force, p1_y_force))

            # Player 2 controls (Arrow keys)
            p2_x_force = 0
            p2_y_force = 0
            if len(self.players) > 1:
                if keys[pygame.K_LEFT]:
                    p2_x_force = -1  # Full left force
                elif keys[pygame.K_RIGHT]:
                    p2_x_force = 1   # Full right force

            actions.append((p2_x_force, p2_y_force))

            # Take game step
            if not self.game_over:
                self.step(actions)

            # Render
            self.render()

        self.close()