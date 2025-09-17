import os
import sys
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage
from stable_baselines3.common.env_util import make_vec_env

# Add the game directory to the system path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_base_files_test"))

from gym_env import BalancingBallEnv

def make_env(render_mode="human", difficulty="medium", level=1):
    """Create an environment function"""
    def _init():
        env = BalancingBallEnv(render_mode=render_mode, difficulty=difficulty, obs_type="game_screen", level=level, window_x=1000, window_y=600, fps=120)
        return env
    return _init

def play_game(model_path, difficulty="medium", level=1, episodes=5):
    """
    Play the game using a trained model
    
    Args:
        model_path: Path to the saved model
        difficulty: Game difficulty level
        episodes: Number of episodes to play
    """
    # Create environment
    env = make_vec_env(
        make_env(render_mode="human", difficulty=difficulty, level=level),
        n_envs=1
    )
    # Load the model
    model = PPO.load(model_path)
    
    for episode in range(episodes):
        obs = env.reset()
        done = False
        total_reward = 0
        step = 0
        
        print(f"Starting episode {episode+1}")
        
        while not done:
            # Get model action
            action, _ = model.predict(obs, deterministic=True)
            
            # Take step in the environment
            obs, reward, done, info = env.step(action)
            
            total_reward += reward[0]
            step += 1
            
            # Break if any environment is done
            if done.any():
                done = True
        
        print(f"Episode {episode+1} finished with reward {total_reward:.2f} after {step} steps")
    
    env.close()

if __name__ == "__main__":
    play_game(
        model_path="./ppo_game_screen_315000_steps_level1",
        difficulty="medium",
        level=2,
        episodes=10
    )
