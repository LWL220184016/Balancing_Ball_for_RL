import os
import sys


# Add the game directory to the system path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from RL.train import Train
from gym_env import BalancingBallEnv
from exceptions import GameClosedException

def make_env(render_mode=None, model_cfg=None):
    """Create an environment function"""
    def _init():
        env = BalancingBallEnv(render_mode=render_mode, model_cfg=model_cfg)
        return env
    return _init

def play_game(training: bool = None, model_path: str = None, episodes: int = None):
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
    train_cfg.render_mode = "human"  # Set render mode to human for visualization

    path = os.path.abspath(__file__)
    msg = f"""
    Already changed render_mode to "{train_cfg.render_mode}" in  {path}. Suitable for testing models on a local computer, and can display the game screen while the model is playing the game
    """
    print(f"\n\033[38;5;220m {msg}\033[0m")

    train_cfg.total_timesteps = 3000

    evaluater = Train(
        model_cfg=model_cfg,
        train_cfg=train_cfg,
        n_envs=1,
        load_model=model_path,
    )

    try:
        if training:
            evaluater.train_ppo()
        else:   
            evaluater.evaluate(episodes, deterministic=True)
    except GameClosedException:
        print("Game was closed by the user. Shutting down gracefully.")
        # 不需要做任何事，程式會自然結束。
        # SB3 的 `learn()` 方法會因為異常而停止，並執行其內部的 finally 清理。
    except KeyboardInterrupt:
        print("\nTraining interrupted by user (Ctrl+C). Shutting down.")
        # 這裡的邏輯可以保留，用於處理終端機的中斷
    finally:
        # 確保在任何情況下都嘗試關閉環境
        # 注意：evaluater.env 可能已經被 SB3 或其他地方關閉了
        print("Final cleanup.")
        # 可以加上檢查，避免重複關閉
        if evaluater and evaluater.env and evaluater.env.unwrapped:
            evaluater.env.close()
        if evaluater and evaluater.eval_env and evaluater.eval_env.unwrapped:
            evaluater.eval_env.close()

    
if __name__ == "__main__":
    # play_game(
    #     model_path="./ppo_game_screen_315000_steps_level1",
    #     episodes=10
    # )


    play_game(
        training=True,
        # model_path="./trained_model/level3/ppo_checkpoint_state_based_850000_steps.zip",
        model_path=None,
        episodes=3
    )
