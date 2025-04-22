import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import gymnasium as gym
import sys

from stable_baselines3 import PPO
from stable_baselines3.common.policies import ActorCriticCnnPolicy
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.evaluation import evaluate_policy

# Add the game directory to the system path
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_base_files_test"))

from classes.gym_env import BalancingBallEnv

# support render_mode: human, rgb_array, rgb_array_and_human, rgb_array_and_human_in_colab
def make_env(render_mode="rgb_array", difficulty="medium"):
    """
    Create and return an environment function to be used with VecEnv
    """
    def _init():
        env = BalancingBallEnv(render_mode=render_mode, difficulty=difficulty)
        return env
    return _init

def train_ppo(
    total_timesteps=1000000,
    learning_rate=0.003,
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
    save_freq=10000,
    log_dir="./logs/",
    model_dir="./models/",
    eval_freq=10000,
    eval_episodes=5,
    difficulty="medium",
    load_model=None,
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
    # Create directories
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    # Setup environments
    # support render_mode: human, rgb_array, rgb_array_and_human, rgb_array_and_human_in_colab
    env = make_vec_env(
        make_env(render_mode="rgb_array_and_human_in_colab", difficulty=difficulty),
        n_envs=n_envs
    )

    # Apply VecTransposeImage to correctly handle image observations
    env = VecTransposeImage(env)

    # Setup evaluation environment
    eval_env = make_vec_env(
        make_env(render_mode="rgb_array_and_human_in_colab", difficulty=difficulty),
        n_envs=1
    )
    eval_env = VecTransposeImage(eval_env)

    # Define policy kwargs if not provided
    if policy_kwargs is None:
        policy_kwargs = {
            "features_extractor_kwargs": {"features_dim": 512},
        }

    # Create the PPO model
    if load_model:
        print(f"Loading model from {load_model}")
        model = PPO.load(
            load_model,
            env=env,
            tensorboard_log=log_dir,
        )
    else:
        model = PPO(
            policy=ActorCriticCnnPolicy,
            env=env,
            learning_rate=learning_rate,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            gamma=gamma,
            gae_lambda=gae_lambda,
            ent_coef=ent_coef,
            vf_coef=vf_coef,
            max_grad_norm=max_grad_norm,
            tensorboard_log=log_dir,
            policy_kwargs=policy_kwargs,
            verbose=1,
        )

    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq // n_envs,  # Divide by n_envs as save_freq is in timesteps
        save_path=model_dir,
        name_prefix="ppo_balancing_ball"
    )

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=model_dir,
        log_path=log_dir,
        eval_freq=eval_freq // n_envs,
        n_eval_episodes=eval_episodes,
        deterministic=True,
        render=False
    )

    # Train the model
    print("Starting training...")
    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_callback, eval_callback],
    )

    # Save the final model
    model.save(f"{model_dir}/ppo_balancing_ball_final")

    print("Training completed!")
    return model

def evaluate(model_path, n_episodes=10, difficulty="medium"):
    """
    Evaluate a trained model

    Args:
        model_path: Path to the saved model
        n_episodes: Number of episodes to evaluate on
        difficulty: Game difficulty level
    """
    # Create environment for evaluation
    env = make_vec_env(
        make_env(render_mode="human", difficulty=difficulty),
        n_envs=1
    )
    env = VecTransposeImage(env)

    # Load the model
    model = PPO.load(model_path)

    # Evaluate
    mean_reward, std_reward = evaluate_policy(
        model,
        env,
        n_eval_episodes=n_episodes,
        deterministic=True,
        render=True
    )

    print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")

    env.close()

  # import argparse

  # parser = argparse.ArgumentParser(description="Train or evaluate PPO agent for Balancing Ball")
  # parser.add_argument("--mode", type=str, default="train", choices=["train", "eval"],
  #                     help="Mode: 'train' to train model, 'eval' to evaluate")
  # parser.add_argument("--timesteps", type=int, default=1000000,
  #                     help="Total timesteps for training")
  # parser.add_argument("--difficulty", type=str, default="medium",
  #                     choices=["easy", "medium", "hard"],
  #                     help="Game difficulty")
  # parser.add_argument("--load_model", type=str, default=None,
  #                     help="Path to model to load for continued training or evaluation")
  # parser.add_argument("--n_envs", type=int, default=4,
  #                     help="Number of parallel environments for training")
  # parser.add_argument("--eval_episodes", type=int, default=5,
  #                     help="Number of episodes for evaluation")

  # args = parser.parse_args()

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