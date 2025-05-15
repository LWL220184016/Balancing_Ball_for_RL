import gymnasium as gym
import numpy as np
from gymnasium import spaces

from classes.balancing_ball_game import BalancingBallGame

class BalancingBallEnv(gym.Env):
    """
    Gymnasium environment for the Balancing Ball game
    """
    metadata = {'render_modes': ['human', 'rgb_array']}

    def __init__(self, 
                 render_mode="rgb_array", 
                 difficulty="medium", 
                 fps=30,
                 obs_type="game_screen", 
                 image_size=(84, 84),
                ):
        """
        render_mode: how to render the environment
            Example: "human" or "rgb_array"
        fps: Frames per second,
            Example: 30
        obs_type: type of observation
            Example: "game_screen" or "state_based"
        image_size: Size to resize images to (height, width)
            Example: (84, 84) - standard for many RL implementations
        """

        super(BalancingBallEnv, self).__init__()

        # Action space: discrete - 0: left, 1: right
        self.action_space = spaces.Discrete(2)

        # Initialize game
        self.window_x = 1000
        self.window_y = 600
        self.platform_shape = "circle"
        self.platform_proportion = 0.333
        
        # Image preprocessing settings
        self.image_size = image_size

        self.stack_size = 3  # Number of frames to stack
        self.observation_stack = []  # Initialize the stack
        self.render_mode = render_mode

        self.game = BalancingBallGame(
            render_mode=render_mode,
            sound_enabled=(render_mode == "human"),
            difficulty=difficulty,
            window_x = self.window_x,
            window_y = self.window_y,
            fps = fps,
            platform_shape = self.platform_shape,
            platform_proportion = self.platform_proportion,
        )

        if obs_type == "game_screen":
            import cv2
            channels = 1
            
            # Image observation space with stacked frames
            self.observation_space = spaces.Box(
                low=0, high=255, 
                shape=(self.image_size[0], self.image_size[1], channels * self.stack_size),
                dtype=np.uint8, 
            )
            self.step = self.step_game_screen
            self.reset = self.reset_game_screen
        elif obs_type == "state_based":
            # State-based observation space: [ball_x, ball_y, ball_vx, ball_vy, platform_x, platform_y, platform_angular_velocity]
            # Normalize values to be between -1 and 1
            self.observation_space = spaces.Box(
                low=np.array([-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]),
                high=np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]),
                dtype=np.float32
            )
            self.step = self.step_state_based
            self.reset = self.reset_state_based
        else:
            raise ValueError("obs_type must be 'game_screen' or 'state_based'")

        # Platform_length /= 2 when for calculate the distance to the
        # center of game window coordinates. The closer you are, the higher the reward.
        self.platform_reward_length = (self.game.platform_length / 2) - 5

        # When the ball is to be 10 points away from the center coordinates,
        # it should be 1 - ((self.platform_length - 10) * self.x_axis_max_reward_rate)
        self.x_axis_max_reward_rate = 0.5 / self.platform_reward_length
    
    def _preprocess_observation(self, observation):
        """Process raw game observation for RL training
        
        Args:
            observation: RGB image from the game
            
        Returns:
            Processed observation ready for RL
        """
        observation = np.transpose(observation, (1, 0, 2))
        
        observation = cv2.cvtColor(observation, cv2.COLOR_RGB2GRAY)
        observation = np.expand_dims(observation, axis=-1)  # Add channel dimension back
            
        # Resize to target size
        if observation.shape[0] != self.image_size[0] or observation.shape[1] != self.image_size[1]:
            # For grayscale, temporarily remove the channel dimension for cv2.resize
            observation = cv2.resize(
                observation.squeeze(-1), 
                (self.image_size[1], self.image_size[0]), 
                interpolation=cv2.INTER_AREA
            )
            observation = np.expand_dims(observation, axis=-1)  # Add channel dimension back
            
        return observation
        
    def step_game_screen(self, action):
        """Take a step in the environment"""
        # Take step in the game
        obs, step_reward, terminated = self.game.step(action)
        
        # Preprocess the observation
        obs = self._preprocess_observation(obs)

        # Stack the frames
        self.observation_stack.append(obs)
        if len(self.observation_stack) > self.stack_size:
            self.observation_stack.pop(0)  # Remove the oldest frame

        # If the stack isn't full yet, pad it with the current frame
        while len(self.observation_stack) < self.stack_size:
            self.observation_stack.insert(0, obs)  # Pad with current frame at the beginning

        stacked_obs = np.concatenate(self.observation_stack, axis=-1)

        # Gymnasium expects (observation, reward, terminated, truncated, info)
        return stacked_obs, step_reward, terminated, False, {}

    def reset_game_screen(self, seed=None, options=None):
        """Reset the environment"""
        super().reset(seed=seed)  # This properly seeds the environment in Gymnasium

        observation = self.game.reset()
        
        # Preprocess the observation
        observation = self._preprocess_observation(observation)

        # Reset the observation stack
        self.observation_stack = []

        # Fill the stack with the initial observation
        for _ in range(self.stack_size):
            self.observation_stack.append(observation)

        # Create stacked observation
        stacked_obs = np.concatenate(self.observation_stack, axis=-1)

        info = {}
        return stacked_obs, info

    def _get_state_based_observation(self):
        """Convert game state to state-based observation for RL agent"""
        # Normalize positions by window dimensions
        ball_x = self.game.dynamic_body.position[0] / self.window_x * 2 - 1  # Convert to [-1, 1]
        ball_y = self.game.dynamic_body.position[1] / self.window_y * 2 - 1  # Convert to [-1, 1]

        # Normalize velocities (assuming max velocity around 1000)
        max_velocity = 1000
        ball_vx = np.clip(self.game.dynamic_body.velocity[0] / max_velocity, -1, 1)
        ball_vy = np.clip(self.game.dynamic_body.velocity[1] / max_velocity, -1, 1)

        # Normalize platform position
        platform_x = self.game.kinematic_body.position[0] / self.window_x * 2 - 1  # Convert to [-1, 1]
        platform_y = self.game.kinematic_body.position[1] / self.window_y * 2 - 1  # Convert to [-1, 1]

        # Normalize angular velocity (assuming max around 10)
        max_angular_velocity = 10
        platform_angular_velocity = np.clip(self.game.kinematic_body.angular_velocity / max_angular_velocity, -1, 1)

        return np.array([
            ball_x,
            ball_y,
            ball_vx,
            ball_vy,
            platform_x,
            platform_y,
            platform_angular_velocity
        ], dtype=np.float32)

    def step_state_based(self, action):
        """Take a step in the environment"""
        # Take step in the game
        _, step_reward, terminated = self.game.step(action)

        # Get state-based observation
        observation = self._get_state_based_observation()

        # Gymnasium expects (observation, reward, terminated, truncated, info)
        return observation, step_reward, terminated, False, {}

    def reset_state_based(self, seed=None, options=None):
        """Reset the environment"""
        super().reset(seed=seed)  # This properly seeds the environment in Gymnasium

        self.game.reset()
        observation = self._get_state_based_observation()

        info = {}
        return observation, info

    def render(self):
        """Render the environment"""
        return self.game.render()

    def close(self):
        """Clean up resources"""
        self.game.close()