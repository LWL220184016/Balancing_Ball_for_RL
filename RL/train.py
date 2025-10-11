# RL/train.py

import sys
import os

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.vec_env import VecNormalize

# Go up one level from the current notebook's directory to the project root
project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import from the project root
from game.gym_env import BalancingBallEnv
from RL.levels.level3.config import model_config, train_config

class Train:
    def __init__(self,
                 model_cfg: model_config=None,
                 train_cfg: train_config=None,
                 n_envs: int=None,
                 load_model=None,
                ):

        # Create directories
        os.makedirs(train_cfg.tensorboard_log, exist_ok=True)
        os.makedirs(train_cfg.model_dir, exist_ok=True)
        self.model_cfg = model_cfg
        self.train_cfg = train_cfg
        self.log_dir = train_cfg.tensorboard_log
        self.model_dir = train_cfg.model_dir
        self.n_envs = n_envs
        self.obs_type = model_cfg.model_obs_type

        # Setup environments
        env = make_vec_env(self.make_env(), n_envs=n_envs)
        self.env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
        
        eval_env = make_vec_env(self.make_env(), n_envs=1)
        self.eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=True, clip_obs=10.)
        self.eval_env.training = False # In evaluation, we don't want to update normalization stats
        self.eval_env.norm_reward = False

        # Create or load the PPO model
        if load_model and os.path.exists(load_model):
            print(f"Loading model from {load_model}")
            self.model = PPO.load(
                load_model,
                env=self.env,
                tensorboard_log=self.log_dir,
            )
            
            # --- 重要：載入 VecNormalize 統計數據 ---
            # 從模型路徑推斷統計數據檔案的路徑（例如 a.zip -> a.pkl）
            stats_path = os.path.splitext(load_model)[0] + ".pkl"
            if os.path.exists(stats_path):
                print(f"Loading VecNormalize stats from: {stats_path}")
                self.env = VecNormalize.load(stats_path, self.env)
                self.eval_env = VecNormalize.load(stats_path, self.eval_env)
                # 確保評估環境保持在非訓練模式
                self.eval_env.training = False
                self.eval_env.norm_reward = False
            else:
                print(f"WARNING: VecNormalize stats not found at {stats_path}. Model performance may be affected.")
        else:
            print("Creating a new model.")
            self.model = PPO(
                env=self.env,
                tensorboard_log=self.log_dir,
                **model_cfg.model_param
            )

        # Setup callbacks
        self.checkpoint_callback = CheckpointCallback(
            save_freq=train_cfg.save_freq // self.n_envs,
            save_path=self.model_dir,
            name_prefix="ppo_checkpoint_" + str(self.obs_type),
            save_vecnormalize=True, # 讓 callback 自動保存正規化數據
        )

        self.eval_callback = EvalCallback(
            self.eval_env,
            best_model_save_path=self.model_dir,
            log_path=self.log_dir,
            eval_freq=train_cfg.eval_freq // self.n_envs,
            n_eval_episodes=train_cfg.eval_episodes,
            deterministic=True,
            render=False
        )

    def make_env(self):
        """Create and return an environment function to be used with VecEnv"""
        def _init():
            env = BalancingBallEnv(
                render_mode=self.train_cfg.render_mode,
                model_cfg=self.model_cfg,
                train_cfg=self.train_cfg,
            )
            return env
        return _init

    def train_ppo(self):
        """
        訓練 PPO agent
        """

        print("\nStarting training... Press Ctrl+C to interrupt and save progress.")
        # 如果是載入模型繼續訓練，設置 reset_num_timesteps=False
        self.model.learn(
            total_timesteps=self.train_cfg.total_timesteps,
            callback=[self.checkpoint_callback, self.eval_callback],
        )
        
        # --- 訓練完成後，保存最終模型和統計數據 ---
        final_model_path = os.path.join(self.model_dir, "ppo_balancing_ball_final")
        self.model.save(final_model_path)
        self.env.save(f"{final_model_path}.pkl")
        print("Training completed!")
        
        return self.model

    def evaluate(self, n_episodes=10, deterministic: bool = None):
        """Evaluate a trained model"""
        mean_reward, std_reward = evaluate_policy(
            self.model,
            self.eval_env, # 使用評估環境
            n_eval_episodes=n_episodes,
            deterministic=deterministic,
            render=True
        )
        print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")
        self.eval_env.close()

    # ... (test_env_with_random_action method remains the same) ...