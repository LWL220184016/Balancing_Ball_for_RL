import numpy as np
import pygame
import time
import cv2
import pymunk
import gymnasium as gym
from gymnasium import spaces

class BallBalanceEnv(gym.Env):
    """
    Environment to train an agent on the balancing ball game.
    """
    metadata = {'render_modes': ['rgb_array']}
    
    def __init__(self, space, bodies, reset_game, window_size=(1000, 600), render_mode=None):
        super().__init__()
        self.space = space
        self.bodies = bodies
        self.reset_game_fn = reset_game
        self.window_size = window_size
        self.render_mode = render_mode
        self.FPS = 60
        
        # Observation space: preprocessed screen images
        self.observation_shape = (84, 84, 1)  # Grayscale image
        self.observation_space = spaces.Box(
            low=0, high=255, shape=self.observation_shape, dtype=np.uint8
        )
        
        # Action space: 0 = left, 1 = right
        self.action_space = spaces.Discrete(2)
        
        # Setup pygame for rendering
        pygame.init()
        self.screen = pygame.Surface(window_size)
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        
        # Game state
        self.game_duration = None
        self.step_count = 0
        self.max_episode_steps = 1000
        
    def reset(self, seed=None):
        """Reset the environment."""
        super().reset(seed=seed)
        self.game_duration = self.reset_game_fn()
        self.step_count = 0
        
        # Return initial observation
        observation = self._get_observation()
        return observation, {}
    
    def step(self, action):
        """Execute action and return new state, reward, done, truncated, info."""
        self.step_count += 1
        
        # Apply action (0 = left, 1 = right)
        dynamic_body = self.bodies.get("player_obj_body")
        if action == 0:  # Left
            dynamic_body.angular_velocity -= 1
        else:  # Right
            dynamic_body.angular_velocity += 1
        
        # Update physics
        self.space.step(1 / self.FPS)
        
        # Get observation
        observation = self._get_observation()
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check if episode is done
        done = False
        truncated = False
        
        # Check if ball fell off screen
        dynamic_body = self.bodies.get("player_obj_body")
        if dynamic_body.position[1] > self.window_size[1]:
            done = True
            reward -= 10  # Penalty for falling
        
        # Truncate if episode is too long
        if self.step_count >= self.max_episode_steps:
            truncated = True
        
        # Info dictionary
        info = {
            "ball_position": dynamic_body.position,
            "ball_velocity": dynamic_body.velocity,
            "platform_rotation": self.bodies.get("env_obj_body").angle,
            "episode_length": self.step_count
        }
        
        return observation, reward, done, truncated, info
    
    def _calculate_reward(self):
        """Calculate reward based on ball position and platform stability."""
        dynamic_body = self.bodies.get("player_obj_body")
        kinematic_body = self.bodies.get("env_obj_body")
        
        # Reward for keeping the ball on the platform
        reward = 0.1
        
        # Extra reward for balancing near the center of the platform
        distance_to_center = abs(dynamic_body.position[0] - self.window_size[0] / 2)
        center_reward = max(0, 1 - (distance_to_center / (self.window_size[0] / 2)))
        reward += 0.05 * center_reward
        
        # Penalty for excessive rotation of the ball
        if abs(dynamic_body.angular_velocity) > 5:
            reward -= 0.01 * abs(dynamic_body.angular_velocity) / 5
        
        return reward
    
    def _get_observation(self):
        """Capture the game screen and preprocess it for the agent."""
        # Render the game to the surface
        self.screen.fill((255, 255, 255))
        self.space.debug_draw(self.draw_options)
        
        # Convert surface to numpy array
        screen_array = pygame.surfarray.array3d(self.screen)
        
        # Convert to grayscale and resize to 84x84
        gray = cv2.cvtColor(screen_array, cv2.COLOR_RGB2GRAY)
        resized = cv2.resize(gray, (84, 84), interpolation=cv2.INTER_AREA)
        
        # Expand dimensions to match observation shape
        observation = np.expand_dims(resized, axis=2)
        
        return observation
    
    def render(self):
        """Render the environment."""
        if self.render_mode == "rgb_array":
            # Return RGB array
            self.screen.fill((255, 255, 255))
            self.space.debug_draw(self.draw_options)
            return pygame.surfarray.array3d(self.screen)
        else:
            return None
        
    def close(self):
        """Close the environment."""
        pygame.quit()
