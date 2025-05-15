import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import gymnasium as gym
import sys

from stable_baselines3 import PPO
from stable_baselines3.common.policies import ActorCriticPolicy, ActorCriticCnnPolicy  # MLP policy instead of CNN
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.evaluation import evaluate_policy

from classes.gym_env import BalancingBallEnv
class Train:
    def __init__(self,
                 learning_rate=0.0003,
                 n_steps=2048,
                 batch_size=64,
                 n_epochs=10,
                 gamma=0.99,
                 gae_lambda=0.95,
                 ent_coef=0.01,
                 vf_coef=0.5,
                 max_grad_norm=0.5,
                 policy_kwargs=None,
                 n_envs=4,
                 difficulty="medium",
                 load_model=None,
                 log_dir="./logs/",
                 model_dir="./models/",
                 obs_type="game_screen", 
                ):

        # Create directories
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(model_dir, exist_ok=True)
        self.log_dir = log_dir
        self.model_dir = model_dir
        self.n_envs = n_envs
        self.obs_type = obs_type

        # Setup environments
        env = make_vec_env(
            self.make_env(render_mode="human", difficulty=difficulty, obs_type=obs_type),
            n_envs=n_envs
        )
        self.env = env  # No need for VecTransposeImage with state-based observations

        # Setup evaluation environment
        eval_env = make_vec_env(
            self.make_env(render_mode="rgb_array", difficulty=difficulty, obs_type=obs_type),
            n_envs=1
        )
        self.eval_env = eval_env  # No need for VecTransposeImage

        # Define policy kwargs if not provided
        if policy_kwargs is None:
            policy_kwargs = {
                "net_arch": [256, 256]  # MLP architecture
            }

        # Create the PPO model
        if load_model:
            print(f"Loading model from {load_model}")
            self.model = PPO.load(
                load_model,
                env=self.env,
                tensorboard_log=log_dir,
            )
        else:
            hyper_param = {
                'learning_rate': 0.0003,
                'gamma': 0.99,
                'clip_range': 0.2,
                'gae_lambda': 0.95,
                'ent_coef': 0.01,
                'vf_coef': 0.5,
            }
            policy = ActorCriticPolicy if obs_type == "game_screen" else ActorCriticCnnPolicy
            print("obs type: ", self.obs_type)
            print("policy: ", policy)
            # MLP policy for state-based observations, CNN policy for image-based observations
            self.model = PPO(
                policy=policy,  
                env=self.env,
                learning_rate=hyper_param["learning_rate"],
                n_steps=n_steps,
                batch_size=batch_size,
                n_epochs=n_epochs,
                gamma=hyper_param["gamma"],
                clip_range=hyper_param["clip_range"],
                gae_lambda=hyper_param["gae_lambda"],
                ent_coef=hyper_param["ent_coef"],
                vf_coef=hyper_param["vf_coef"],
                max_grad_norm=max_grad_norm,
                tensorboard_log=log_dir,
                policy_kwargs=policy_kwargs,
                verbose=1,
            )

    def make_env(self, render_mode="rgb_array", difficulty="medium", obs_type="game_screen"):
        """
        Create and return an environment function to be used with VecEnv
        """
        def _init():
            env = BalancingBallEnv(render_mode=render_mode, difficulty=difficulty, obs_type=obs_type)
            return env
        return _init

    def train_ppo(self,
                  total_timesteps=1000000,
                  save_freq=10000,
                  eval_freq=10000,
                  eval_episodes=5,
                 ):
        """
        Train a PPO agent to play the Balancing Ball game

        Args:
            total_timesteps: Total number of steps to train for
            n_envs: Number of parallel environments
            save_freq: How often to save checkpoints (in timesteps)
            log_dir: Directory for tensorboard logs
            model_dir: Directory to save models
            eval_freq: How often to evaluate the model (in timesteps)
            eval_episodes: Number of episodes to evaluate on
            difficulty: Game difficulty level
            load_model: Path to model to load for continued training
        """

        # Setup callbacks
        checkpoint_callback = CheckpointCallback(
            save_freq=save_freq // self.n_envs,  # Divide by n_envs as save_freq is in timesteps
            save_path=self.model_dir,
            name_prefix="ppo_balancing_ball_" + str(self.obs_type),
        )

        eval_callback = EvalCallback(
            self.eval_env,
            best_model_save_path=self.model_dir,
            log_path=self.log_dir,
            eval_freq=eval_freq // self.n_envs,
            n_eval_episodes=eval_episodes,
            deterministic=True,
            render=False
        )

        # Train the model
        print("Starting training...")
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=[checkpoint_callback, eval_callback],
        )

        # Save the final model
        self.model.save(f"{self.model_dir}/ppo_balancing_ball_final_" + str(self.obs_type))

        print("Training completed!")
        return self.model

    def evaluate(self, n_episodes=10, difficulty="medium"):
        """
        Evaluate a trained model

        Args:
            n_episodes: Number of episodes to evaluate on
            difficulty: Game difficulty level
        """
        # Evaluate
        mean_reward, std_reward = evaluate_policy(
            self.model,
            self.env,
            n_eval_episodes=n_episodes,
            deterministic=True,
            render=True
        )

        print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")

        self.env.close()


# if args.mode == "train":
#     train_ppo(
#         total_timesteps=args.timesteps,
#         difficulty=args.difficulty,
#         n_envs=args.n_envs,
#         load_model=args.load_model,
#         eval_episodes=args.eval_episodes,
#     )
# else:
#     if args.load_model is None:
#         print("Error: Must provide --load_model for evaluation")
#     else:
#         evaluate(
#             model_path=args.load_model,
#             n_episodes=args.eval_episodes,
#             difficulty=args.difficulty
#         )