import gymnasium as gym
import numpy as np
from gymnasium import spaces
import cv2

from game_config import GameConfig

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
                 render_mode: str = None,
                 model_cfg: str = None,  # <class 'RL.levels.level3.config.model_config'>
                 train_cfg: str = None,  # <class 'RL.levels.level3.config.train_config'>
                ):
        """
        envonment initialization
        Args:
            render_mode (str): The mode to render the game. Options are 'human', 'rgb_array', 'rgb_array_and_human_in_colab'.
            level (int): The game level to load.
            fps (int): Frames per second for the game.
            obs_type (str): Type of observation. "game_screen" for image-based, "state_based" for state vector.
            image_size (tuple): Size to which game screen images are resized (height, width).
        """

        super(BalancingBallEnv, self).__init__()
        print("Initializing BalancingBallEnv...")

        # Initialize game

        # Image preprocessing settings
        self.image_size = model_cfg.image_size
        self.action_size = model_cfg.action_size

        self.stack_size = 3  # Number of frames to stack
        self.observation_stack = []  # Initialize the stack
        self.render_mode = render_mode

        self.game = BalancingBallGame(
            render_mode=render_mode,
            sound_enabled=(render_mode == "human"),
            max_episode_step = train_cfg.max_episode_step,
            level_config_path=model_cfg.level_config_path,
            level = model_cfg.level,
            fps = model_cfg.fps,
        )
        
        self.window_x = GameConfig.SCREEN_WIDTH
        self.window_y = GameConfig.SCREEN_HEIGHT

        self.num_players = self.game.num_players

        # Action space: continuous - Box space for horizontal force [-1.0, 1.0] for each player
        self.action_space = spaces.Box(low=model_cfg.action_space_low, high=model_cfg.action_space_high, shape=(model_cfg.action_size,), dtype=np.float32)

        if model_cfg.model_obs_type == "game_screen":
            channels = 1

            # Image observation space with stacked frames
            self.observation_space = spaces.Box(
                low=0, high=255,
                shape=(self.image_size[0], self.image_size[1], channels * self.stack_size),
                dtype=np.uint8,
            )
            self.step = self.step_game_screen
            self.reset = self.reset_game_screen
        elif model_cfg.model_obs_type == "state_based":
            obs_size = model_cfg.obs_size
            self.observation_space = spaces.Box(
                low=np.full(obs_size, -1.0),
                high=np.full(obs_size, 1.0),
                dtype=np.float32
            )
            self.step = self.step_state_based
            self.reset = self.reset_state_based
        else:
            raise ValueError(f"obs_type: {model_cfg.model_obs_type} must be 'game_screen' or 'state_based'")

    def _preprocess_observation_game_screen(self):
        """Process raw game observation for RL training

        Args:
            observation: RGB image from the game

        Returns:
            Processed observation ready for RL
        """

        observation = self.game._get_observation_game_screen()
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

        step_rewards, terminated = self.game.step(action)
        obs = self._preprocess_observation_game_screen()

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

        self.game.reset()
        observation = self._preprocess_observation_game_screen()

        # Reset the observation stack
        self.observation_stack = []

        # Fill the stack with the initial observation
        for _ in range(self.stack_size):
            self.observation_stack.append(observation)

        # Create stacked observation
        stacked_obs = np.concatenate(self.observation_stack, axis=-1)

        info = {}
        return stacked_obs, info

    def _preprocess_observation_state_base(self):
        """Convert game state to state-based observation for RL agent"""
        obs = self.game._get_observation_state_based()

        return obs

    def step_state_based(self, action):
        """Take a step in the environment with state-based observations"""
        # Ensure action is the right shape
        if isinstance(action, (int, float)):
            action = [action]
        elif len(action) / self.action_size != self.num_players:
            raise ValueError(f"Action: {action} length {len(action)} does not match number of players {self.num_players}")

        # Take step in the game
        # transformed_action = [[action[0], action[1], (abs(action[2] * self.window_x), abs(action[3] * self.window_y))]] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        transformed_action = [[0, 0, (abs(float(action[0] * self.window_x)), abs(float(action[1] * self.window_y)))]] # TODO 因爲 game 的 step 是根據玩家人數遍歷 action 的 list，如果只有一層 list，就會把一個玩家的 action 拆分而不是完整的 action 傳進去
        _, step_rewards, terminated = self.game.step(transformed_action)

        # Get state-based observation
        observation = self._preprocess_observation_state_base()

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
        observation = self._preprocess_observation_state_base()

        info = {}
        return observation, info

    def render(self):
        """Render the environment"""
        return self.game.render()

    def close(self):
        """Clean up resources"""
        self.game.close()

    def get_game(self):
        return self.game