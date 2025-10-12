import sys
import os
from typing import Callable

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


# <<< 新增：學習率排程函數 >>>
def get_step_lr_schedule(
    initial_lr: float,
    drop_factor: float,
    drop_progress_threshold: float
) -> Callable[[float], float]:
    """
    創建一個階梯式學習率排程 (Step Learning Rate Schedule)。

    :param initial_lr: 初始學習率。
    :param drop_factor: 學習率下降的倍數（例如 0.1 表示下降到原來的 10%）。
    :param drop_progress_threshold: 訓練進度達到多少時開始下降（例如 0.5 表示訓練一半後）。
    :return: 一個 schedule 函數，可傳入 PPO 模型。
    """
    def schedule(progress_remaining: float) -> float:
        """
        這個函數會被 SB3 調用，progress_remaining 從 1.0 逐漸下降到 0.0。
        """
        # 當剩餘進度小於等於閾值時，降低學習率
        # (1.0 - progress_remaining) 代表已完成的訓練進度
        if (1.0 - progress_remaining) >= drop_progress_threshold:
            return initial_lr * drop_factor
        else:
            return initial_lr

    return schedule

# --- 您也可以考慮使用更平滑的「線性衰減」，這是非常常用的策略 ---
def get_linear_lr_schedule(
    initial_lr: float,
    final_lr: float
) -> Callable[[float], float]:
    """
    創建一個線性學習率排程 (Linear Learning Rate Schedule)。
    """
    def schedule(progress_remaining: float) -> float:
        return final_lr + (initial_lr - final_lr) * progress_remaining
    return schedule


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
        self.load_model = load_model

        # Setup environments
        env = make_vec_env(self.make_env(), n_envs=n_envs)
        self.env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
        
        eval_env = make_vec_env(self.make_env(), n_envs=1)
        self.eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=True, clip_obs=10.)
        self.eval_env.training = False 
        self.eval_env.norm_reward = False

        # <<< 修改：在創建模型前，將學習率設置為排程函數 >>>
        # 假設您的 model_param 是一個字典
        # 從 config 中取出初始學習率
        initial_learning_rate = self.model_cfg.model_param.get('learning_rate') # 默認值以防萬一

        # --- 選擇您想要的排程方式 ---
        # 方案一：階梯式下降 (Step Decay)
        # 例如：訓練 50% 後，學習率下降為原來的 10%
        lr_schedule = get_step_lr_schedule(
            initial_lr=initial_learning_rate,
            drop_factor=0.1, 
            drop_progress_threshold=0.5
        )

        # 方案二：線性下降 (Linear Decay) - 推薦嘗試
        # lr_schedule = get_linear_lr_schedule(
        #     initial_lr=initial_learning_rate,
        #     final_lr=1e-6 # 設置一個很小的最終學習率
        # )

        # 更新模型參數字典，使用排程函數替換固定的學習率
        self.model_cfg.model_param['learning_rate'] = lr_schedule
        # <<< 修改結束 >>>

        # Create or load the PPO model
        if load_model and os.path.exists(load_model):
            print(f"Loading model from {load_model}")
            self.model = model_cfg.rl_algorithm.load(
                load_model,
                env=self.env,
                tensorboard_log=self.log_dir,
                # 當載入模型時，SB3 會自動處理學習率排程的狀態，但最好也傳入
                custom_objects={"learning_rate": lr_schedule}
            )
            
            stats_path = os.path.splitext(load_model)[0] + ".pkl"
            if os.path.exists(stats_path):
                print(f"Loading VecNormalize stats from: {stats_path}")
                self.env = VecNormalize.load(stats_path, self.env)
                self.eval_env = VecNormalize.load(stats_path, self.eval_env)
                self.eval_env.training = False
                self.eval_env.norm_reward = False
            else:
                print(f"WARNING: VecNormalize stats not found at {stats_path}. Model performance may be affected.")
        else:
            print("Creating a new model with learning rate schedule.")
            self.model = model_cfg.rl_algorithm(
                env=self.env,
                tensorboard_log=self.log_dir,
                # 這裡會傳入包含學習率排程的參數
                **model_cfg.model_param 
            )

        # Setup callbacks
        self.checkpoint_callback = CheckpointCallback(
            save_freq=train_cfg.save_freq // self.n_envs,
            save_path=self.model_dir,
            name_prefix= self.model_cfg.rl_algorithm.__name__ + "_checkpoint_" + str(self.obs_type),
            save_vecnormalize=True,
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

        reset_num_timesteps = False
        if isinstance(self.load_model, str):
            if os.path.exists(self.load_model):
                reset_num_timesteps = True
        self.model.learn(
            total_timesteps=self.train_cfg.total_timesteps,
            callback=[self.checkpoint_callback, self.eval_callback],
            reset_num_timesteps=reset_num_timesteps # 繼續訓練時不要重置步數
        )
        
        final_model_path = os.path.join(self.model_dir, self.model_cfg.rl_algorithm.__name__ + "_balancing_ball_final")
        self.model.save(final_model_path)
        self.env.save(f"{final_model_path}.pkl")
        print("Training completed!")
        
        return self.model

    def evaluate(self, n_episodes=10, deterministic: bool = None):
        """Evaluate a trained model"""
        mean_reward, std_reward = evaluate_policy(
            self.model,
            self.eval_env,
            n_eval_episodes=n_episodes,
            deterministic=deterministic,
            render=True
        )
        print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")
        self.eval_env.close()