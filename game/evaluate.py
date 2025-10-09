import os
import sys


# Add the game directory to the system path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from RL.train import Train
from gym_env import BalancingBallEnv

def make_env(render_mode=None, model_cfg=None):
    """Create an environment function"""
    def _init():
        env = BalancingBallEnv(render_mode=render_mode, model_cfg=model_cfg)
        return env
    return _init

def play_game(model_path: str = None, episodes: int = None):
    """
    Play the game using a trained model
    
    Args:
        model_path: Path to the saved model
        episodes: Number of episodes to play
    """
    # Create environment
    from RL.levels.level3.config import model_config, train_config

    model_cfg = model_config()
    train_cfg = train_config()

    evaluater = Train(
        model_cfg=model_cfg,
        train_cfg=train_cfg,
        n_envs=1,
        load_model=model_path,
    )

    evaluater.evaluate(episodes)

if __name__ == "__main__":
    # play_game(
    #     model_path="./ppo_game_screen_315000_steps_level1",
    #     episodes=10
    # )


    play_game(
        model_path="./trained_model/level3/best_model.zip",
        episodes=1
    )

    