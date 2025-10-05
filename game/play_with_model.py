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

def make_env(render_mode=None, model_cfg=None):
    """Create an environment function"""
    def _init():
        env = BalancingBallEnv(render_mode=render_mode, model_cfg=model_cfg, window_x=1000, window_y=600)
        return env
    return _init

def play_game(model_path, episodes=5):
    """
    Play the game using a trained model
    
    Args:
        model_path: Path to the saved model
        episodes: Number of episodes to play
    """
    # Create environment
    from RL.levels.level3.config import model_config
    import pygame  # 導入 pygame

    env = BalancingBallEnv(
        render_mode="human",
        model_cfg=model_config,
        window_x=1000,
        window_y=1000
    )
    # Load the model
    model = PPO.load(model_path)
    
    for episode in range(episodes):
        obs, info = env.reset()
        done = False
        total_reward = 0
        step = 0
        
        print(f"Starting episode {episode+1}")
        
        while not done:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True # 如果點擊關閉按鈕，則結束迴圈

                if done: # 檢查是否需要提前退出
                    break
            # Get model action
            action, _ = model.predict(obs, deterministic=True)
            
            # Take step in the environment
            obs, reward, done, info, _ = env.step(action)
            
            total_reward += reward
            step += 1
            
        
        print(f"Episode {episode+1} finished with reward {total_reward:.2f} after {step} steps")
    
    env.close()

if __name__ == "__main__":
    # play_game(
    #     model_path="./ppo_game_screen_315000_steps_level1",
    #     episodes=10
    # )


    play_game(
        model_path="./ppo_balancing_ball_state_based_80000_steps",
        episodes=5
    )

    