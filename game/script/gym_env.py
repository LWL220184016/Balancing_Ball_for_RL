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
        self.image_size = getattr(model_cfg, 'image_size', (0, 0)) 
        self.frame_skipping = getattr(model_cfg, 'frame_skipping', 0) 

        self.stack_size = model_cfg.stack_size  # Number of frames to stack
        self.render_mode = render_mode
        self.seed = train_cfg.seed
        self.num_rl_agents = getattr(train_cfg, 'num_agents', 1)
        self.player_role_id = getattr(train_cfg, 'player_role_id')

        self.game = BalancingBallGame(
            render_mode=render_mode,
            obs_width=self.image_size[0],
            obs_height=self.image_size[1],
            sound_enabled=(render_mode == "human"),
            max_episode_step = train_cfg.max_episode_step,
            level_config_path=model_cfg.level_config_path,
            level = model_cfg.level,
            sub_level=0, # 實際上應該是期望模型能游玩 level 中的所有 sub_level
            capture_per_second = None,
        )
        self.window_x = GameConfig.SCREEN_WIDTH
        self.window_y = GameConfig.SCREEN_HEIGHT
        self.num_players = self.game.num_players

        players_role_ids = []
        self.agent_ids = []
        for i in range(self.num_players):
            if i < self.num_rl_agents:
                players_role_ids.append(f"{self.player_role_id}{i}")
                self.agent_ids.append(f"{self.player_role_id}{i}")
            else:
                players_role_ids.append(f"bot_player{i}")

        self.game.assign_players(players_role_ids)
        

        # Action space: continuous - Box space for horizontal force [-1.0, 1.0] for each player

        action_space = schema_to_gym_space(GameConfig.ACTION_SPACE_CONFIG)
        self.action_space = {agent_id: action_space for agent_id in self.agent_ids}
        # self.action_space = spaces.Box(low=model_cfg.action_space_low, high=model_cfg.action_space_high, shape=(model_cfg.action_size,), dtype=np.float32)
   
        # 定義圖像空間 (共用)
        screen_space = spaces.Box(
            low=0, high=255,
            shape=(self.image_size[0], self.image_size[1], model_cfg.channels * self.stack_size),
            dtype=np.uint8,
        )
        
        # 定義向量空間 (共用，假設 obs_size 存在於 cfg)
        # 如果 model_cfg 沒有 obs_size，你需要手動指定一個數字，例如 10
        vec_obs_size = getattr(model_cfg, 'state_obs_size', 1) 
        vector_space = spaces.Box(
            low=-1.0, high=1.0, 
            shape=(vec_obs_size,), 
            dtype=np.float32
        )

        if model_cfg.model_obs_type == "game_screen":
            # 純圖像模式 (原有邏輯)
            self.observation_space = {agent_id: screen_space for agent_id in self.agent_ids}
            self.step = self.step_game_screen
            self.reset = self.reset_game_screen
            
        elif model_cfg.model_obs_type == "state_based":
            # 純向量模式 (原有邏輯)
            self.observation_space = {agent_id: vector_space for agent_id in self.agent_ids}
            self.step = self.step_state_based
            self.reset = self.reset_state_based

        elif model_cfg.model_obs_type == "mixed":
            # [NEW] 混合模式 (Mixed Observation)
            print("Using Mixed Observation Space (Screen + State)")
            
            # 定義 Dict Space
            mixed_space = spaces.Dict({
                "screen": screen_space,  # 圖像部分 (Stacked)
                "state": vector_space    # 向量部分 (Current)
            })
            
            self.observation_space = {agent_id: mixed_space for agent_id in self.agent_ids}
            
            # 指向新的 step/reset 方法
            self.step = self.step_mixed
            self.reset = self.reset_mixed
        
        else:
            raise ValueError(f"Unknown obs_type: {model_cfg.model_obs_type}")

        self.game.render()
        self.reset()
        print("self.observation_space: ", self.observation_space)

    def reset_mixed(self, seed=None, options=None):
        super().reset(seed=self.seed)
        self.game.reset()
        
        # 1. 處理圖像 (初始化 Stack)
        img_obs = self._preprocess_observation_game_screen()
        self.observation_stack_dict = {}
        
        stacked_img_obs = {}
        for agent_id, img in img_obs.items():
            self.observation_stack_dict[agent_id] = []
            # 填滿 stack
            for _ in range(self.stack_size):
                self.observation_stack_dict[agent_id].append(img)
            
            # Concatenate
            stacked_img_obs[agent_id] = np.concatenate(self.observation_stack_dict[agent_id], axis=-1)

        # 2. 處理向量
        vec_obs = self._preprocess_observation_state_base() # 確保這返回的是 {agent_id: numpy_array}

        # 3. 組合 Dict
        mixed_obs = {}
        for agent_id in self.agent_ids:
            # 容錯處理：如果某個 agent 在 reset 後立刻沒有 obs (通常不會發生)
            agent_img = stacked_img_obs.get(agent_id)
            agent_vec = vec_obs.get(agent_id)
            
            mixed_obs[agent_id] = {
                "screen": agent_img,
                "state": agent_vec
            }

        info = {}
        return mixed_obs, info

    def step_mixed(self, action):
        processed_action = _numpy_to_python(action)

        terminated = False
        step_rewards = {agent_id: 0.0 for agent_id in self.agent_ids}
        for n in range(self.frame_skipping):
            if terminated:
                break

            _step_rewards, terminated = self.game.step(processed_action)
            for key, reward in _step_rewards.items():
                step_rewards[key] += reward
        
        # 1. 獲取新數據
        new_img_obs = self._preprocess_observation_game_screen()
        new_vec_obs = self._preprocess_observation_state_base()
        
        mixed_obs = {}
        
        # 2. 更新 Stack 並組合
        for agent_id in self.agent_ids:
            if "bot" in agent_id:
                continue

            # 更新圖像 Stack
            current_stack = self.observation_stack_dict[agent_id]
            current_stack.append(new_img_obs[agent_id])
            current_stack.pop(0) # 移除最舊的
            stacked_img = np.concatenate(current_stack, axis=-1)

            # 獲取向量
            vec = new_vec_obs[agent_id]

            mixed_obs[agent_id] = {
                "screen": stacked_img,
                "state": vec
            }

        # 3. 處理 done, reward, info
        terminateds = {agent_id: terminated for agent_id in self.agent_ids}
        terminateds["__all__"] = terminated
        truncateds = {agent_id: False for agent_id in self.agent_ids}
        truncateds["__all__"] = False

        info = {}
        for agent_id in self.agent_ids:
            info[agent_id] = {"step_reward": step_rewards.get(agent_id, 0)}
        
        info["__common__"] = {
            'winner': getattr(self.game, "winner_role_id"),
            'scores': getattr(self.game, 'score', [0])
        }

        return mixed_obs, step_rewards, terminateds, truncateds, info

# -------------------------------------------------------------------------

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

# -------------------------------------------------------------------------

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

# -------------------------------------------------------------------------

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
