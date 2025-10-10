import torch
import pathlib 

from stable_baselines3.common.policies import ActorCriticPolicy, ActorCriticCnnPolicy  # MLP policy instead of CNN

class model_config:
    model_obs_type="state_based"
    level=3  # Game level
    num_player=1
    fps=360

    level_config_path=str(pathlib.Path(__file__).parent.resolve()) + f"/level_{level}_default_cfg.json"
    
    action_space_low=0  # Minimum action value
    action_space_high=1.0   # Maximum action value
    action_num = 1 # now many actions model can choose
    action_size = 2 # how many values model need to output (might be 2 values for one action)
    obs_size = 8

    image_size=(84, 84) if model_obs_type == "game_screen" else None  # Observation image size

    if model_obs_type == "game_screen":
        policy_kwargs={
                    "features_extractor_kwargs": {"features_dim": 512},
                    "net_arch": [512, 512, 256],  # 增加網絡深度以處理複雜策略
                    "activation_fn": torch.nn.ReLU,
                }
    elif model_obs_type == "state_based":
        policy_kwargs={
                    "net_arch": [512, 512, 256],  # 增加網絡深度以處理複雜策略
                    "activation_fn": torch.nn.ReLU,
                }

    model_param={
        # ActorCriticCnnPolicy if for game_screen, ActorCriticPolicy for state_based
        "policy": ActorCriticPolicy if model_obs_type == "state_based" else ActorCriticCnnPolicy,  

        "learning_rate": 0.0003,
        "n_steps": 4096,
        "batch_size": 64,
        "n_epochs": 10,
        "gamma": 0.995,
        "clip_range": 0.2,
        "gae_lambda": 0.98,
        "ent_coef": 0.15,
        "vf_coef": 0.5,
        "max_grad_norm": 0.5,
        "policy_kwargs": policy_kwargs,
        "verbose": 1,
    }

class train_config:
    total_timesteps=5000000
    max_episode_step=50000  # Maximum steps per episode
    save_freq=10000
    eval_freq=10000
    eval_episodes=5
    agent_num=2
    tensorboard_log="./logs/"
    model_dir="./models/"
    render_mode="headless"  

    msg = """
    render_mode = "human" Suitable for testing models on a local computer, and can display the game screen while the model is playing the game
    render_mode = "headless" Suitable for training models on Google Colab, significantly reducing computational load and speeding up training
    """
    print(f"\n\033[38;5;220m {msg}\033[0m")
    