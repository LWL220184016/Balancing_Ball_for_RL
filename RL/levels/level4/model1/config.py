import pathlib
# <<< 導入正確的 SAC 策略網路 >>>
# MlpPolicy 用於狀態輸入 (state_based)
# CnnPolicy 用於圖像輸入 (game_screen)

class model_config:
    level=4
    level_config_path=str(pathlib.Path(__file__).parent.resolve()) + f"/level_{level}_default_cfg.json"
    
class train_config:
    total_timesteps=5000000
    max_episode_step=500000  # Maximum steps per episode
    save_freq=50000
    eval_freq=10000
    eval_episodes=5
    tensorboard_log="./logs/"
    model_dir="./models/"
    render_mode="headless"  

    msg = """
    render_mode = "human" Suitable for testing models on a local computer, and can display the game screen while the model is playing the game
    render_mode = "headless" Suitable for training models on Google Colab, significantly reducing computational load and speeding up training
    """
    print(f"\n\033[38;5;220m {msg}\033[0m")
    