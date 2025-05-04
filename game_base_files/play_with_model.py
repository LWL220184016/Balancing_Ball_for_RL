import os
import sys
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage

# Add the game directory to the system path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_base_files_test"))

from gym_env import BalancingBallEnv

def make_env(render_mode="human", difficulty="medium"):
    """Create an environment function"""
    def _init():
        env = BalancingBallEnv(render_mode=render_mode, difficulty=difficulty)
        return env
    return _init

def play_game(model_path, difficulty="medium", episodes=5):
    """
    Play the game using a trained model
    
    Args:
        model_path: Path to the saved model
        difficulty: Game difficulty level
        episodes: Number of episodes to play
    """
    # Create environment
    env = make_vec_env(
        make_env(render_mode="human", difficulty=difficulty),
        n_envs=1
    )
    env = VecTransposeImage(env)
    
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
    import argparse
    
    parser = argparse.ArgumentParser(description="Play Balancing Ball with a trained model")
    parser.add_argument("--model", type=str, required=True,
                        help="Path to the saved model")
    parser.add_argument("--difficulty", type=str, default="medium", 
                        choices=["easy", "medium", "hard"],
                        help="Game difficulty")
    parser.add_argument("--episodes", type=int, default=5,
                        help="Number of episodes to play")
    
    args = parser.parse_args()
    
    play_game(
        model_path=args.model,
        difficulty=args.difficulty,
        episodes=args.episodes
    )
