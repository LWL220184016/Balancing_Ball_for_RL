import pymunk
import pygame
import time
import numpy as np
import os
import numpy as np
import base64
import datetime
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
    BALL_COLOR = (255, 213, 79)  # Bright yellow ball
    PLATFORM_COLOR = (235, 64, 52)  # Red platform

    def __init__(self,
                 render_mode: str = "human",
                 sound_enabled: bool = True,
                 difficulty: str = "medium",
                 window_x: int = 1000,
                 window_y: int = 600,
                 max_step: int = 30000,
                 player_configs: dict = None,
                 reward_staying_alive: float = 0.1,
                 reward_ball_centered: float = 0.2,
                 penalty_falling: float = -10.0,
                 level: int = 2,
                 fps: int = 120,
                 platform_proportion: int = 0.4,
                 capture_per_second: int = None,
                 collision_reward: float = 5.0,  # Increased collision reward
                 speed_reward_multiplier: float = 0.01,  # Reward for maintaining speed
                 opponent_fall_bonus: float = 15.0,  # Bonus for causing opponent to fall
                 survival_bonus: float = 0.5,  # Bonus for staying alive when opponent falls
                 platform_distance_penalty: float = 0.02,  # Penalty for being far from platform center
                ):
        """
        Initialize the balancing ball game.

        Args:
            render_mode: "human" for visible window, "rgb_array" for gym env, "headless" for no rendering
            sound_enabled: Whether to enable sound effects
            difficulty: Game difficulty level ("easy", "medium", "hard")
            max_step: 1 step = 1/fps, if fps = 120, 1 step = 1/120
            reward_staying_alive: float = 0.1,
            reward_ball_centered: float = 0.2,
            penalty_falling: float = -10.0,
            fps: frame per second
            platform_proportion: platform_length = window_x * platform_proportion
            capture_per_second: save game screen as a image every second, None means no capture
            collision_reward: Reward bonus for causing opponent to fall through collision
            speed_reward_multiplier: Multiplier for speed-based rewards
        """
        # Game parameters
        self.max_step = max_step
        self.reward_staying_alive = reward_staying_alive
        self.reward_ball_centered = reward_ball_centered
        self.penalty_falling = penalty_falling
        self.fps = fps
        self.window_x = window_x
        self.window_y = window_y
        self.collision_reward = collision_reward
        self.speed_reward_multiplier = speed_reward_multiplier
        self.opponent_fall_bonus = opponent_fall_bonus
        self.survival_bonus = survival_bonus
        self.platform_distance_penalty = platform_distance_penalty

        self.recorder = Recorder("game_history_record")
        self.render_mode = render_mode
        self.sound_enabled = sound_enabled
        self.difficulty = difficulty

        platform_length = int(window_x * platform_proportion)
        self._get_x_axis_max_reward_rate(platform_length)

        # Initialize physics space
        self.space = pymunk.Space()
        self.space.gravity = (0, 9810)
        self.space.damping = 0.9

        self.level = get_level(level, self.space, player_configs)
        self.player_ball_speed = self.level.player_ball_speed
        players, platforms = self.level.setup(self.window_x, self.window_y)
        self.dynamic_body_players = []
        self.kinematic_body_platforms = []
        self.players_color = []
        self.player_alive = []  # Track which players are still alive

        for i, player in enumerate(players):
            self.dynamic_body_players.append(player["body"])
            self.players_color.append(player["ball_color"])
            self.player_alive.append(True)

        for platform in platforms:
            self.kinematic_body_platforms.append(platform["body"])

        self.ball_radius = players[0]["ball_radius"]
        self.platform_length = platforms[0]["platform_length"]
        self.num_players = len(players)

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

        # Set difficulty parameters
        self._apply_difficulty()
        self.capture_per_second = capture_per_second

        # Create folders for captures if needed
        # CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        CURRENT_DIR = "."
        os.makedirs(os.path.dirname(CURRENT_DIR + "/capture/"), exist_ok=True)

        if self.num_players > 2:
            raise ValueError("Warning!!! collision reward calculation in step() can only work for two players now")


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

    def _apply_difficulty(self):
        """Apply difficulty settings to the game"""
        if self.difficulty == "easy":
            self.max_platform_speed = 1.5
            self.ball_elasticity = 0.5
        elif self.difficulty == "medium":
            self.max_platform_speed = 2.5
            self.ball_elasticity = 0.7
        else:  # hard
            self.max_platform_speed = 3.5
            self.ball_elasticity = 0.9

        # self.circle.shape.elasticity = self.ball_elasticity

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
        self.player_alive = [True] * self.num_players
        self.last_speeds = [0] * self.num_players
        self.players_fell_this_step = [False] * self.num_players

        # Return initial observation
        return self._get_observation()

    def step(self, pactions: list = []) -> Tuple[np.ndarray, list, bool, Dict]:
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
        # Reset collision and fall tracking for this step
        self.level.collision_occurred = False
        self.players_fell_this_step = [False] * self.num_players
        
        # 需要保留直到移除舊模型，詳情看函數說明
        # actions = pactions if isinstance(pactions, list) else [pactions]
        # actions = self.calculate_player_speed_old(actions)


        actions = self.calculate_player_speed(pactions)

        # 遍歷所有玩家
        for i, player_body in enumerate(self.dynamic_body_players):
            # 如果 actions 列表不夠長，則對後續玩家使用 0 作為預設動作
            action_value = actions[i] if i < len(actions) else 0
            
            # 直接施加對應方向的力
            force_vector = pymunk.Vec2d(action_value, 0)
            player_body.apply_force_at_world_point(force_vector, player_body.position)

            # # 施加角速度
            # player_body.angular_velocity += action_value
            # self.dynamic_body_players[1].angular_velocity += p1action

        self.level.action()

        # Step the physics simulation
        self.space.step(1/self.fps)

        # Check game state
        self.steps += 1
        terminated = False
        rewards = [0] * self.num_players
        player_velocities = []

        # Check collision reward if available
        collision_occurred = getattr(self.level, 'collision_occurred', False)
        collision_impulse_1 = getattr(self.level, 'collision_impulse_1', 0)
        collision_impulse_2 = getattr(self.level, 'collision_impulse_2', 0)

        # Check if balls fall off screen and calculate rewards
        alive_count = 0
        platform_center_x = self.kinematic_body_platforms[0].position[0]
        
        for i, player in enumerate(self.dynamic_body_players):
            if not self.player_alive[i]:
                continue

            ball_x = player.position[0]
            ball_y = player.position[1]
            player_velocities.append(player.velocity)

            # Check if player falls
            if (ball_y > self.kinematic_body_platforms[0].position[1] + 50 or
                ball_x < 0 or ball_x > self.window_x):

                self.player_alive[i] = False
                self.players_fell_this_step[i] = True
                rewards[i] = self.penalty_falling

                if self.sound_enabled and self.sound_fall:
                    self.sound_fall.play()
            else:
                alive_count += 1
                
                # 基礎生存獎勵
                survival_reward = self.reward_staying_alive

                # 速度獎勵 - 鼓勵保持移動
                current_speed = abs(player.velocity[0]) + abs(player.velocity[1])
                speed_reward = min(current_speed * self.speed_reward_multiplier, 0.1)  # 限制最大速度獎勵
                
                # 平台中心獎勵 - 鼓勵靠近平台中心但不要太極端
                center_reward = self._calculate_center_reward(ball_x)
                
                # 平台距離懲罰 - 距離平台中心太遠會有小懲罰
                distance_from_platform = abs(ball_x - platform_center_x)
                distance_penalty = -min(distance_from_platform * self.platform_distance_penalty, 0.5)

                rewards[i] = survival_reward + speed_reward + center_reward + distance_penalty
                self.score[i] += rewards[i]
                self.last_speeds[i] = current_speed

        # 處理碰撞獎勵 - 更智能的獎勵系統
        if collision_occurred and len(player_velocities) >= 2:
            # 基於碰撞時的衝量差距給予獎勵
            impulse_diff = collision_impulse_1 - collision_impulse_2
            
            # 獎勵較高衝量的玩家，懲罰較低衝量的玩家
            if abs(impulse_diff) > 0.1:  # 避免微小差距的獎勵
                collision_reward_1 = impulse_diff * self.collision_reward * 0.1
                collision_reward_2 = -impulse_diff * self.collision_reward * 0.1
                
                # 限制碰撞獎勵的範圍
                collision_reward_1 = np.clip(collision_reward_1, -2.0, 2.0)
                collision_reward_2 = np.clip(collision_reward_2, -2.0, 2.0)
                
                if self.player_alive[0]:
                    rewards[0] += collision_reward_1
                if self.player_alive[1]:
                    rewards[1] += collision_reward_2
                    
                print(f"Collision rewards: P1: {collision_reward_1:.2f}, P2: {collision_reward_2:.2f}")

        # 處理對手掉落的獎勵
        for i in range(self.num_players):
            if self.player_alive[i]:  # 如果這個玩家還活著
                # 檢查是否有對手在這步掉落
                opponents_fell = any(self.players_fell_this_step[j] for j in range(self.num_players) if j != i)
                if opponents_fell:
                    rewards[i] += self.opponent_fall_bonus  # 獲得擊敗對手的獎勵
                    print(f"Player {i+1} gets opponent fall bonus: {self.opponent_fall_bonus}")

        # Check if game should end
        if alive_count <= 1 or self.steps >= self.max_step:
            print("Final Scores: ", self.score)
            terminated = True
            self.game_over = True

            # Determine winner (last player alive or highest score)
            if alive_count == 1:
                self.winner = next(i for i in range(self.num_players) if self.player_alive[i])
                # Give bonus to winner
                rewards[self.winner] += self.survival_bonus * self.steps / 100  # 生存時間越長獎勵越多
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

        return self._get_observation(), rewards, terminated

    def _get_observation(self) -> np.ndarray:
        """Convert game state to observation for RL agent"""
        # update particles and draw them
        screen_data = self.render() # 获取数据

        if self.capture_per_second is not None and self.frame_count % self.capture_per_second == 0:  # Every second at 60 FPS
            pygame.image.save(self.screen, f"capture/frame_{self.frame_count/60}.png")

        self.frame_count += 1
        return screen_data

    def _calculate_center_reward(self, ball_x):
        """Calculate reward based on how close ball is to center"""
        distance_from_center = abs(ball_x - self.window_x/2)
        if distance_from_center < self.reward_width:
            normalized_distance = distance_from_center / self.reward_width
            return self.reward_ball_centered * (1.0 - normalized_distance)
        return 0

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
        for i in range(len(self.dynamic_body_players)):
            if self.player_alive[i]:  # Only draw alive players
                player_body = self.dynamic_body_players[i]
                ball_pos = (int(player_body.position.x), int(player_body.position.y))
                pygame.draw.circle(self.screen, self.players_color[i], ball_pos, self.ball_radius)
                pygame.draw.circle(self.screen, (255, 255, 255), ball_pos, self.ball_radius, 2)

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
        score_texts = [f"P{i+1}: {self.score[i]:.1f}" for i in range(self.num_players)]

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
            color = self.players_color[i] if i < len(self.players_color) else (255, 255, 255)
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

    def _get_x_axis_max_reward_rate(self, platform_length):
        """
        ((self.platform_length / 2) - 5) for calculate the distance to the
        center of game window coordinates. The closer you are, the higher the reward.

        When the ball is to be 10 points away from the center coordinates,
        it should be 1 - ((self.platform_length - 10) * self.x_axis_max_reward_rate)
        """
        self.reward_width = (platform_length / 2) - 5
        self.x_axis_max_reward_rate = 2 / self.reward_width
        print("self.x_axis_max_reward_rate: ", self.x_axis_max_reward_rate)

    def _reward_calculator(self, ball_x):
        # score & reward
        step_reward = 1/100

        rw = abs(ball_x - self.window_x/2)
        if rw < self.reward_width:
            x_axis_reward_rate = 1 + ((self.reward_width - abs(ball_x - self.window_x/2)) * self.x_axis_max_reward_rate)
            step_reward = self.steps * 0.01 * x_axis_reward_rate  # Simplified reward calculation

            if self.steps % 500 == 0:
                step_reward += self.steps/100
                print("check point: ", self.steps/500)

            return step_reward
        else:
            return 0

    def close(self):
        """Close the game and clean up resources"""
        if self.render_mode in ["human", "rgb_array"]:
            pygame.quit()

    def calculate_player_speed(self, moving_direction: list = []):
        """
        Calculate the speed of the player ball for continuous action space

        The new trained model uses a continuous action space ranging from -1.0 to 1.0,
        where negative values represent leftward force and positive values represent rightward force.
        """
        for i in range(len(moving_direction)):
            if moving_direction[i] < -1.0 or moving_direction[i] > 1.0:
                raise ValueError(f"Invalid action: {moving_direction}. Action must be in range [-1.0, 1.0].")

            moving_direction[i] = moving_direction[i] * self.player_ball_speed

        return moving_direction

    def calculate_player_speed_old(self, moving_direction: list = []):
        """
        Calculate the speed of the player ball

        新訓練的模型是連續動作空間，範圍包含正數和負數，
        但是早期訓練的模型只能輸出 0 和 1，分別代表向左和向右，因此有必要保留這個函數直到移除舊模型
        """
        # In order to fit the model action space, the model can currently only output 0 and 1, so 2 is no action

        for i in range(len(moving_direction)):
            if moving_direction[i] == 0:
                moving_direction[i] = self.player_ball_speed * -1

            elif moving_direction[i] == 1:
                moving_direction[i] = self.player_ball_speed

            elif moving_direction[i] == 2:
                moving_direction[i] = 0

            else:
                raise ValueError(f"Invalid action: {moving_direction}. Action must be 0 (left), 1 (right), or 2 (no action).")

        return moving_direction

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

            # Player 1 controls (Arrow keys)
            if keys[pygame.K_LEFT]:
                actions.append(-1)  # Full left force
            elif keys[pygame.K_RIGHT]:
                actions.append(1)   # Full right force
            else:
                actions.append(0)   # No force

            # Player 2 controls (WASD)
            if len(self.dynamic_body_players) > 1:
                if keys[pygame.K_a]:
                    actions.append(-1)  # Full left force
                elif keys[pygame.K_d]:
                    actions.append(1)   # Full right force
                else:
                    actions.append(0)   # No force

            # Take game step
            if not self.game_over:
                self.step(actions)

            # Render
            self.render()

        self.close()