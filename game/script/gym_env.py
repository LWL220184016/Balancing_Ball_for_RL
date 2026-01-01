import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

import gymnasium as gym
import numpy as np
import cv2

from gymnasium import spaces
from script.game_config import GameConfig
from script.schema_to_gym_space import schema_to_gym_space
from ray.rllib.env.multi_agent_env import MultiAgentEnv

try:
    from balancing_ball_game import BalancingBallGame
except ImportError:
    from script.balancing_ball_game import BalancingBallGame

class BalancingBallEnv(MultiAgentEnv):
    """
    Gymnasium environment for the Balancing Ball game with continuous action space
    """

    def __init__(self,
                 render_mode: str = None,
                 model_cfg: str = None,  # <class 'RL.levels.level3.config.model_config'>
                 train_cfg: str = None,  # <class 'RL.levels.level3.config.train_config'>
                ):
        """
        envonment initialization
        Args:
            render_mode (str): The mode to render the game. Options are 'human', 'headless'.
            level (int): The game level to load.
            fps (int): Frames per second for the game.
            obs_type (str): Type of observation. "game_screen" for image-based, "state_based" for state vector.
            image_size (tuple): Size to which game screen images are resized (height, width).
        """

        super(BalancingBallEnv, self).__init__()
        print("Initializing BalancingBallEnv...")

        # Initialize game

        # Image preprocessing settings
        self.image_size = model_cfg.image_size if model_cfg.image_size else (0, 0)

        self.stack_size = model_cfg.stack_size  # Number of frames to stack
        self.observation_stack_dict: dict[list, list] = {} # Initialize the stack
        self.render_mode = render_mode
        self.seed = train_cfg.seed

        self.game = BalancingBallGame(
            render_mode=render_mode,
            obs_width=self.image_size[0],
            obs_height=self.image_size[1],
            sound_enabled=(render_mode == "human"),
            max_episode_step = train_cfg.max_episode_step,
            level_config_path=model_cfg.level_config_path,
            level = model_cfg.level,
            capture_per_second = None,
        )
        self.window_x = GameConfig.SCREEN_WIDTH
        self.window_y = GameConfig.SCREEN_HEIGHT
        self.num_players = self.game.num_players

        players_role_ids = []
        for i in range(self.num_players):
            players_role_ids.append(f"RL_player{i}")

        self.game.assign_players(players_role_ids)
        

        # Action space: continuous - Box space for horizontal force [-1.0, 1.0] for each player

        action_space = schema_to_gym_space(GameConfig.ACTION_SPACE_CONFIG)
        # self.action_space = spaces.Box(low=model_cfg.action_space_low, high=model_cfg.action_space_high, shape=(model_cfg.action_size,), dtype=np.float32)

        if model_cfg.model_obs_type == "game_screen":
            # Image observation space with stacked frames
            observation_space = spaces.Box(
                low=0, high=255,
                shape=(self.image_size[0], self.image_size[1], model_cfg.channels * self.stack_size),
                dtype=np.uint8,
            )
            self.step = self.step_game_screen
            self.reset = self.reset_game_screen
            
            self.game.render()
            obs = self.game._get_observation_game_screen()
            for key, obs in obs.items():
                self.observation_stack_dict[key] = []
                while len(self.observation_stack_dict[key]) < self.stack_size:
                    self.observation_stack_dict[key].insert(0, obs)  # Pad with current frame at the beginning

            self.agent_ids = [f"RL_player{i}" for i in range(self.num_players)]
            self.observation_space = {
                agent_id: observation_space for agent_id in self.agent_ids
            }
            self.action_space = {
                agent_id: action_space for agent_id in self.agent_ids
            }
            print("self.observation_space: ", self.observation_space)
            print("self.action_space: ", self.action_space)
            
        elif model_cfg.model_obs_type == "state_based":
            raise ValueError(f"obs_type: {model_cfg.model_obs_type} is out of support")

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
        # 一個環境多於一個 Agent，返回的是 dict
        observation = self.game._get_observation_game_screen()
        # observation = np.transpose(observation, (1, 0, 2))

        # observation = cv2.cvtColor(observation, cv2.COLOR_RGB2GRAY)
        # observation = np.expand_dims(observation, axis=-1)  # Add channel dimension back

        return observation

    def step_game_screen(self, action):
        """Take a step in the environment with continuous actions"""
        
        processed_action = _numpy_to_python(action)
        step_rewards, terminated = self.game.step(processed_action)
        new_obs = self._preprocess_observation_game_screen()

        # Stack the frames
        stacked_obs = {}
        for key, obs in self.observation_stack_dict.items():
            obs.append(new_obs[key])
            obs.pop(0)
            stacked_obs[key] = np.concatenate(obs, axis=-1)

        # Gymnasium expects (observation, reward, terminated, truncated, info)
        terminateds = {agent_id: terminated for agent_id in stacked_obs.keys()}
        terminateds["__all__"] = terminated
        
        truncateds = {agent_id: False for agent_id in stacked_obs.keys()}
        truncateds["__all__"] = False

        info = {}
        
        # 1. Provide info for each active agent
        for agent_id in stacked_obs.keys():
            info[agent_id] = {
                # You can put agent-specific info here if needed
                "step_reward": step_rewards.get(agent_id, 0) 
            }

        # 2. Use "__common__" for global game state information
        info["__common__"] = {
            'winner': getattr(self.game.winner, 'role_id', None),
            'scores': getattr(self.game, 'score', [0])
        }


        return stacked_obs, step_rewards, terminateds, truncateds, info

    def reset_game_screen(self, seed=None, options=None):
        """Reset the environment"""
        super().reset(seed=self.seed)  # This properly seeds the environment in Gymnasium

        self.game.reset()
        observation = self._preprocess_observation_game_screen()

        # Reset the observation stack
        self.observation_stack_dict = {}

        stacked_obs = {}
        for key, obs in observation.items():
            self.observation_stack_dict[key] = []
            self.observation_stack_dict[key].append(obs)
            # If the stack isn't full yet, pad it with the current frame
            while len(self.observation_stack_dict[key]) < self.stack_size:
                self.observation_stack_dict[key].insert(0, obs)  # Pad with current frame at the beginning

        # Create stacked observation
            stacked_obs[key] = np.concatenate(self.observation_stack_dict[key], axis=-1)

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
        transformed_action = [{"Collision": (abs(float(action[0] * self.window_x)), abs(float(action[1] * self.window_y)))}] # TODO 因爲 game 的 step 是根據玩家人數遍歷 action 的 list，如果只有一層 list，就會把一個玩家的 action 拆分而不是完整的 action 傳進去
        step_rewards, terminated = self.game.step(transformed_action)

        # Get state-based observation
        observation = self._preprocess_observation_state_base()

        # For multi-agent, return sum of rewards
        total_reward = sum(step_rewards) if isinstance(step_rewards, list) else step_rewards

        info = {
            'rewards': step_rewards if isinstance(step_rewards, list) else [step_rewards],
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

    def close(self):
        """Clean up resources"""
        self.game.close()

    def get_game(self):
        return self.game


def _numpy_to_python(data):
    """遞歸地將 dict 或 list 中的 numpy 數據轉換為 python 原生類型"""
    if isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, dict):
        return {k: _numpy_to_python(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_numpy_to_python(v) for v in data]
    return data
