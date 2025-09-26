import gymnasium as gym
import numpy as np
from gymnasium import spaces
import cv2

try:
    from balancing_ball_game import BalancingBallGame
except ImportError:
    from game.balancing_ball_game import BalancingBallGame

class BalancingBallEnv(gym.Env):
    """
    Gymnasium environment for the Balancing Ball game with continuous action space
    """
    metadata = {'render_modes': ['human', 'rgb_array', 'rgb_array_and_human_in_colab']}

    def __init__(self,
                 render_mode="rgb_array",
                 level=2,
                 fps=30,
                 obs_type="game_screen",
                 image_size=(84, 84),
                 window_x = 300,
                 window_y = 180
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

        
        # Initialize game
        self.window_x = window_x
        self.window_y = window_y

        # Image preprocessing settings
        self.image_size = image_size

        self.stack_size = 3  # Number of frames to stack
        self.observation_stack = []  # Initialize the stack
        self.render_mode = render_mode

        self.game = BalancingBallGame(
            render_mode=render_mode,
            sound_enabled=(render_mode == "human"),
            window_x = self.window_x,
            window_y = self.window_y,
            level = level,
            fps = fps,
        )

        self.num_players = self.game.num_players

        # Action space: continuous - Box space for horizontal force [-1.0, 1.0] for each player
        if self.num_players == 1:
            self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        else:
            self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(self.num_players,), dtype=np.float32)


        if obs_type == "game_screen":
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
            # State-based observation space for multi-player:
            # [ball1_x, ball1_y, ball1_vx, ball1_vy, ball2_x, ball2_y, ball2_vx, ball2_vy, platform_x, platform_y, platform_angular_velocity]
            obs_size = 4 * self.num_players + 3  # 4 values per player + 3 platform values
            self.observation_space = spaces.Box(
                low=np.full(obs_size, -1.0),
                high=np.full(obs_size, 1.0),
                dtype=np.float32
            )
            self.step = self.step_state_based
            self.reset = self.reset_state_based
        else:
            raise ValueError("obs_type must be 'game_screen' or 'state_based'")

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
        """Take a step in the environment with continuous actions"""
        # Ensure action is the right shape
        if isinstance(action, (int, float)):
            action = [action]
        elif len(action) != self.num_players:
            # Pad or truncate action to match number of players
            if len(action) < self.num_players:
                action = list(action) + [0.0] * (self.num_players - len(action))
            else:
                action = action[:self.num_players]

        # Take step in the game
        obs, step_rewards, terminated = self.game.step(action)

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

        # For multi-agent, return sum of rewards or individual rewards based on your preference
        # Here we return the sum for single-agent training on multi-player game
        total_reward = sum(step_rewards) if isinstance(step_rewards, list) else step_rewards

        # Gymnasium expects (observation, reward, terminated, truncated, info)
        info = {
            'individual_rewards': step_rewards if isinstance(step_rewards, list) else [step_rewards],
            'winner': getattr(self.game, 'winner', None),
            'scores': getattr(self.game, 'score', [0])
        }

        return stacked_obs, total_reward, terminated, False, info

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
        obs = []

        # Add each player's state
        for i, player_body in enumerate(self.game.dynamic_body_players):
            # Normalize positions by window dimensions
            ball_x = player_body.position[0] / self.window_x * 2 - 1  # Convert to [-1, 1]
            ball_y = player_body.position[1] / self.window_y * 2 - 1  # Convert to [-1, 1]

            # Normalize velocities (assuming max velocity around 1000)
            max_velocity = 1000
            ball_vx = np.clip(player_body.velocity[0] / max_velocity, -1, 1)
            ball_vy = np.clip(player_body.velocity[1] / max_velocity, -1, 1)

            obs.extend([ball_x, ball_y, ball_vx, ball_vy])

        # Add platform state
        platform_body = self.game.kinematic_body_platforms[0]
        platform_x = platform_body.position[0] / self.window_x * 2 - 1  # Convert to [-1, 1]
        platform_y = platform_body.position[1] / self.window_y * 2 - 1  # Convert to [-1, 1]

        # Normalize angular velocity (assuming max around 10)
        max_angular_velocity = 10
        platform_angular_velocity = np.clip(platform_body.angular_velocity / max_angular_velocity, -1, 1)

        obs.extend([platform_x, platform_y, platform_angular_velocity])

        return np.array(obs, dtype=np.float32)

    def step_state_based(self, action):
        """Take a step in the environment with state-based observations"""
        # Ensure action is the right shape
        if isinstance(action, (int, float)):
            action = [action]
        elif len(action) != self.num_players:
            # Pad or truncate action to match number of players
            if len(action) < self.num_players:
                action = list(action) + [0.0] * (self.num_players - len(action))
            else:
                action = action[:self.num_players]

        # Take step in the game
        _, step_rewards, terminated = self.game.step(action)

        # Get state-based observation
        observation = self._get_state_based_observation()

        # For multi-agent, return sum of rewards
        total_reward = sum(step_rewards) if isinstance(step_rewards, list) else step_rewards

        info = {
            'individual_rewards': step_rewards if isinstance(step_rewards, list) else [step_rewards],
            'winner': getattr(self.game, 'winner', None),
            'scores': getattr(self.game, 'score', [0])
        }

        # Gymnasium expects (observation, reward, terminated, truncated, info)
        return observation, total_reward, terminated, False, info

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