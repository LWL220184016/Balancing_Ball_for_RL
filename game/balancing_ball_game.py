import pymunk
import pygame
import time
import os
import base64
import numpy as np
import sys
import IPython.display as ipd

from typing import Dict, Tuple, Optional
# from IPython.display import display, Image, clear_output
from io import BytesIO

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
 
from game.record import Recorder
from game.levels.get_levels import get_level
from game.levels.levels import Levels
from game.collision_handle import CollisionHandler
from game.role.player import Player
from game.role.platform import Platform
from game.role.roles import Role
from game.levels.rewards.reward_calculator import RewardCalculator
from exceptions import GameClosedException

class BalancingBallGame:
    """
    A physics-based balancing ball game that can run standalone or be used as a Gym environment.
    """
    # Game constants

    # Visual settings for indie style
    BACKGROUND_COLOR = (41, 50, 65)  # Dark blue background TODO Hard code

    def __init__(self,
                 render_mode: str = None,
                 sound_enabled: bool = True,
                 max_episode_step: int = None,
                 collision_type: dict = None,
                 player_configs: dict = None,
                 platform_configs: dict = None,
                 environment_configs: dict = None,
                 level_config_path: str = None,
                 level: int = None,
                 fps: int = None,
                 capture_per_second: int = None,
                ):
        """
        Initialize the balancing ball game.

        Args:
            render_mode: "human" for visible window, "rgb_array" for gym env, "headless" for no rendering
            sound_enabled: Whether to enable sound effects
            max_episode_step: 1 step = 1/fps, if fps = 120, 1 step = 1/120
            fps: frame per second
            capture_per_second: save game screen as a image every second, None means no capture
        """
        # Game parameters
        self.max_episode_step = max_episode_step
        self.fps = fps

        self.recorder = Recorder("game_history_record")
        self.render_mode = render_mode
        self.sound_enabled = sound_enabled

        # Initialize physics space
        self.space = pymunk.Space()
        self.collision_handler = CollisionHandler(self.space)


        self.level: Levels = get_level(
            level=level, 
            game=self,
            collision_type=collision_type, 
            player_configs=player_configs, 
            platform_configs=platform_configs, 
            environment_configs=environment_configs,
            level_config_path=level_config_path
        )

        self.players: list[Player]
        self.platforms: list[Platform]
        self.entities: list[Role]
        self.reward_calculator: RewardCalculator
        self.players, self.platforms, self.entities, self.reward_calculator = self.level.setup(self.window_x, self.window_y)
        self.num_players = len(self.players)

        self.collision_handler.set_players(self.players)
        self.collision_handler.set_platforms(self.platforms)
        self.collision_handler.set_entities(self.entities)
        self.collision_handler.setup_default_collision_handlers() # 只调用一次！

        # Game state tracking
        self.steps = 0
        self.start_time = time.time()
        self.end_time = self.start_time
        self.game_over = False
        self.score = [0] * self.num_players  # Total Score for each player
        self.winner = None
        self.last_speeds = [0] * self.num_players  # Track last speed for each player
        self.step_rewards = [0] * self.num_players  # Rewards obtained in the last step
        self.step_action = None
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
            raise ValueError("Invalid render mode. Choose from 'human', 'rgb_array', 'rgb_array_and_human', 'rgb_array_and_human_in_colab'.")

        self.clock = pygame.time.Clock()

        # Create custom draw options for indie style

    def _load_sounds(self):
        """Load game sound effects"""
        try:
            pygame.mixer.init()
            self.sound_bounce = pygame.mixer.Sound("assets/bounce.wav") if os.path.exists("assets/bounce.wav") else None
            self.sound_fall = pygame.mixer.Sound("assets/fall.wav") if os.path.exists("assets/fall.wav") else None

            if not self.sound_bounce or not self.sound_fall:
                print("Sound files not found, disabling sound.")
                self.sound_enabled = False
        except Exception:
            print("Sound loading error")
            self.sound_enabled = False
            pass

    def reset(self) -> np.ndarray:
        """Reset the game state and return the initial observation"""
        # Reset physics objects
        self.level.reset()
        self.reward_calculator.reset()

        # Reset game state
        self.steps = 0
        self.start_time = time.time()
        self.game_over = False
        self.score = [0] * self.num_players
        self.winner = None
        self.last_speeds = [0] * self.num_players

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

        self.level.status_reset_step()

        # Step the physics simulation
        self.space.step(1/self.fps)

        # 在物理糢擬后執行動作會導致環境數據過時，但是當 FPS 較高時，這種影響可以忽略不計
        # 而且不得不這麽做的原因是碰撞檢測的回調函數只能在 step 之後執行
        
        # 需要保留直到移除舊模型，詳情看函數說明
        # actions = pactions if isinstance(pactions, list) else [pactions]
        # actions = self.calculate_player_speed_old(actions)
        self.step_action = pactions
        for i, player in enumerate(self.players):
            player.perform_action(pactions[i], self.steps)

        self.add_step(1)
        rewards, terminated = self.reward()
        self.step_rewards = rewards
        self.handle_pygame_events()

        rewards, terminated = self.level.action(rewards, terminated)

        return rewards, terminated 

    def reward(self):
        """
        Calculate and return the reward for the current state.
        """

        # 和玩家存活相關的檢查必須在最上面，因爲後續獎勵計算依賴於玩家是否存活
        rewards, alive_count = self.reward_calculator.calculate_rewards()
        # if self.sound_enabled and self.sound_fall and num_of_players_fell_this_step > 0:
        #     self.sound_fall.play()

        # 處理玩家與實體的碰撞獎勵，包含每個 Step 的狀態重設

        # Check if game should end
        terminated = False
        if alive_count == 0 or (alive_count == 1 and self.num_players > 1) or self.steps >= self.max_episode_step:
            terminated = True
            self.game_over = True

            # Determine winner (last player alive or highest score)
            if alive_count == 1 and self.num_players > 1:
                self.winner = next(i for i in range(self.num_players) if self.players[i].get_is_alive()) 
                # Give bonus to winner
                self.players[self.winner].add_reward_per_step(0.5 * self.steps / 100)  # 生存時間越長獎勵越多 TODO Hard code
                self.score[self.winner] += self.players[self.winner].get_reward_per_step()
            elif self.steps == self.max_episode_step:
                # Game ended due to max steps, winner is highest score
                self.winner = np.argmax(self.score)
            else:
                self.winner = None

        rewards = [0] * self.num_players
        for i, player in enumerate(self.players):
            rewards[i] = player.get_reward_per_step()
            self.score[i] += rewards[i]

        if self.game_over:
            result = {
                "game_total_duration": f"{time.time() - self.start_time:.2f}",
                "scores": self.score,
                "winner": self.winner,
                "steps": self.steps
            }
            self.recorder.add_no_limit(result)

        return rewards, terminated

    def _get_observation_game_screen(self) -> np.ndarray:
        """Convert game state to observation for RL agent"""
        # update particles and draw them

        if isinstance(self.capture_per_second, int) and self.frame_count % self.capture_per_second == 0:  # Every second at 60 FPS
            pygame.image.save(self.screen, f"capture/frame_{self.frame_count/60}.png")

            self.frame_count += 1
        return self.screen_data
    
    def _get_observation_state_based(self) -> np.ndarray:
        """Public method to get the current observation without taking a step"""
        obs = self.level._get_observation_state_based()

        return obs

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
            return None

        elif self.render_mode == "rgb_array":
            # Return RGB array for gym environment
            self.screen_data = pygame.surfarray.array3d(self.screen)
            return None

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
            
            self.screen_data = pygame.surfarray.array3d(self.screen)
            return None
        else:
            pass

    def _draw_indie_style(self):
        """Draw game objects with indie game aesthetic"""
        # Draw players
        for player in self.players:
            if player.get_is_alive():
                player._draw_indie_style(self.screen)

        for platform in self.platforms:
            platform._draw_indie_style(self.screen) 
        
        for entity in self.entities:
            if isinstance(entity, list):
                for e in entity:
                    e._draw_indie_style(self.screen)
            else:
                entity._draw_indie_style(self.screen)

    def _draw_game_info(self):
        """Draw game information on screen"""
        # Create texts
        time_text = f"Time: {self.end_time - self.start_time:.1f}, steps: {self.steps}/{self.max_episode_step}"
        score_texts = [f"P{i+1}: {self.score[i]:.1f} + {self.step_rewards[i]} Health: {player.get_health():.1f}" for i, player in enumerate(self.players)]

        # Render texts
        time_surface = self.font.render(time_text, True, (255, 255, 255))  # TODO Hard code
        score_surfaces = [self.font.render(text, True, (255, 255, 255)) for text in score_texts]

        # Draw text backgrounds and texts
        pygame.draw.rect(self.screen, (0, 0, 0, 128),
                        (5, 5, time_surface.get_width() + 10, time_surface.get_height() + 5))
        self.screen.blit(time_surface, (10, 10))

        # Draw scores
        y_offset = 40
        for i, surface in enumerate(score_surfaces):
            color = self.players[i].get_color() if self.players[i].get_is_alive() else (100, 100, 100)
            pygame.draw.rect(self.screen, (0, 0, 0, 128),
                            (5, y_offset, surface.get_width() + 10, surface.get_height() + 5))
            colored_surface = self.font.render(score_texts[i], True, color)
            self.screen.blit(colored_surface, (10, y_offset))
            y_offset += 30

        # Draw game over screen
        if self.game_over:
            if self.winner is not None:
                game_over_text = f"WINNER: Player {self.winner + 1} - Press R to restart"
            elif self.num_players == 1:
                game_over_text = "GAME OVER - Press R to restart"
            elif self.steps == self.max_episode_step:
                game_over_text = f"Time limit reached. Winner by score: Player {self.winner + 1}"
            else:
                game_over_text = "DRAW - Press R to restart"

            print("Final Scores: ", self.score, " total step: ", self.steps) 
            print(game_over_text)
            game_over_surface = self.font.render(game_over_text, True, (255, 255, 255))

            # Draw semi-transparent background
            overlay = pygame.Surface((self.window_x, self.window_y), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))

            # Draw text
            self.screen.blit(game_over_surface,
                           (self.window_x/2 - game_over_surface.get_width()/2,
                            self.window_y/2 - game_over_surface.get_height()/2))
        else:
            self.end_time = time.time()

    def close(self):
        """Close the game and clean up resources"""
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
        
        try:
            from human_control import HumanControl
        except ImportError:
            from game.human_control import HumanControl
            
        self.human_control = HumanControl(self)

        self.run = True
        while self.run:
            # Handle events
            actions = self.human_control.get_player_actions()

            # Take game step
            if not self.game_over:
                rewards, terminated = self.step([actions])

        self.close()
        
    def handle_pygame_events(self) -> bool:
        """
        處理 Pygame 事件。
        如果偵測到關閉事件，則清理 Pygame 資源並引發一個自訂異常。
        """
        self.render()
        if self.render_mode == "human":
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Close button pressed. Signaling for graceful shutdown.")
                    self.close()  # 關閉 Pygame
                    self.run = False
                    raise GameClosedException("User closed the game window.") # <--- 修改點

    def add_step(self, steps: int = None):
        self.steps += steps

    def get_players(self):
        return self.players
    
    def get_num_players(self):
        return self.num_players
    
    def get_platforms(self):
        return self.platforms
    
    def get_game_over(self):
        return self.game_over
    
    def get_windows_size(self) -> Tuple[int, int]:
        return self.window_x, self.window_y
    
    def get_space(self):
        return self.space

    def get_collision_handler(self):
        return self.collision_handler

    def get_step(self):
        return self.steps
    
    def get_fps(self):
        return self.fps
    
    def get_step_action(self):
        return self.step_action

    def set_windows_size(self, window_x: int, window_y: int):
        self.window_x = window_x
        self.window_y = window_y
        
        # Initialize Pygame if needed
        if self.render_mode in ["human", "rgb_array", "rgb_array_and_human", "rgb_array_and_human_in_colab"]:
            self._setup_pygame()
        else:
            print("render_mode is not human or rgb_array, so no pygame setup.")

    def set_step_rewards(self, rewards: list):
        self.step_rewards = rewards