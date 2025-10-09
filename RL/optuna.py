import os
import sys
import optuna

from stable_baselines3 import PPO
from stable_baselines3.common.policies import ActorCriticPolicy, ActorCriticCnnPolicy  # MLP policy instead of CNN
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.evaluation import evaluate_policy

# Go up one level from the current notebook's directory to the project root
project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import from the project root
from game.gym_env import BalancingBallEnv
from RL.levels.level3.config import model_config, train_config

class Optuna_optimize:
    def __init__(self, obs_type: str = None, level: int = None):
        self.obs_type = obs_type
        self.env = make_vec_env(
            self.make_env(render_mode="rgb_array", obs_type=self.obs_type),
            n_envs=1
        )
        self.level=level

    def make_env(self,
                 render_mode: str = None,
                 model_cfg: str = None
                ):
        """
        Create and return an environment function to be used with VecEnv
        """
        def _init():
            env = BalancingBallEnv(
                render_mode=render_mode,
                model_cfg=model_cfg
            )
            return env
        return _init

    def optuna_parameter_tuning(self, n_trials):
        print("You are using optuna for automatic parameter tuning, it will create a new model")

        pruner = optuna.pruners.HyperbandPruner(
            min_resource=100,        # 最小资源量
            max_resource='auto',   # 最大资源量 ('auto' 或 整数)
            reduction_factor=3     # 折减因子 (eta)
        )

        # 建立 study 物件，並指定剪枝器
        study = optuna.create_study(direction='maximize', pruner=pruner)

        # 執行優化
        try:
            study.optimize(self.objective, n_trials=n_trials)

            # 分析結果
            print("最佳試驗的超參數：", study.best_trial.params)
            print("最佳試驗的平均回報：", study.best_trial.value)

            import pandas as pd
            df = study.trials_dataframe()
            print(df.head())
        finally:
            self.env.close()
            del self.env


    def objective(self, trial):
        import gc

        # 1. 建議超參數 - Adjusted for continuous action space
        learning_rate = trial.suggest_float('learning_rate', 1e-5, 1e-3, log=True)
        gamma = trial.suggest_float('gamma', 0.95, 0.999)
        clip_range = trial.suggest_float('clip_range', 0.1, 0.3)
        gae_lambda = trial.suggest_float('gae_lambda', 0.8, 0.99)
        ent_coef = trial.suggest_float('ent_coef', 0.005, 0.02)  # Lower for continuous actions
        vf_coef = trial.suggest_float('vf_coef', 0.1, 1)
        # features_dim = trial.suggest_categorical('features_dim', [128, 256, 512])

        policy_kwargs = {
            # "features_extractor_kwargs": {"features_dim": features_dim},
            "net_arch": [256, 256],  # Architecture for continuous actions
        }

        n_steps=2048
        batch_size=64
        n_epochs=10
        max_grad_norm=0.5

        policy = ActorCriticCnnPolicy if self.obs_type == "game_screen" else ActorCriticPolicy
        print("obs type: ", self.obs_type)
        print("policy: ", policy)

        # 3. 建立模型 - PPO for continuous action space
        model = PPO(
                policy=policy,
                env=self.env,
                learning_rate=learning_rate,
                n_steps=n_steps,
                batch_size=batch_size,
                n_epochs=n_epochs,
                gamma=gamma,
                clip_range=clip_range,
                gae_lambda=gae_lambda,
                ent_coef=ent_coef,
                vf_coef=vf_coef,
                max_grad_norm=max_grad_norm,
                tensorboard_log=None,
                policy_kwargs=policy_kwargs,
                verbose=0,
            )

        try:
            # 4. 訓練模型
            model.learn(total_timesteps=50000)  # Increased timesteps for adversarial training
            # 5. 評估模型
            mean_reward = evaluate_policy(model, self.env, n_eval_episodes=10)[0]
        finally:
            # Always cleanup
            del model
            gc.collect()

            if TPU_AVAILABLE:
                import torch_xla.core.xla_model as xm
                xm.mark_step()

        return mean_reward