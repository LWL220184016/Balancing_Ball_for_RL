import torch

from stable_baselines3.common.policies import ActorCriticPolicy, ActorCriticCnnPolicy  # MLP policy instead of CNN

class model_config:
    model_obs_type="state_based"
    level=3  # Game level
    num_player=1
    fps=360
    
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
        "policy": ActorCriticPolicy,  

        "learning_rate": 0.0003,
        "n_steps": 4096,
        "batch_size": 64,
        "n_epochs": 10,
        "gamma": 0.995,
        "clip_range": 0.15,
        "gae_lambda": 0.98,
        "ent_coef": 0.1,
        "vf_coef": 0.5,
        "max_grad_norm": 0.5,
        "policy_kwargs": policy_kwargs,
        "verbose": 1,
    }
    player_configs = [
        {
            "shape_type": "circle",
            "size": [
                0.03
            ],
            "shape_mass": 1,
            "shape_friction": 100,
            "shape_elasticity": 0.8,
            "default_position": [
                0.5,
                0.6
            ],
            "default_velocity": [
                0,
                0
            ],
            "abilities": [
                "Collision"
            ],
            "health": 10,
            "color": [
                255,
                213,
                79
            ]
        }
    ]

class train_config:
    total_timesteps=1000000
    max_episode_step=50000  # Maximum steps per episode
    save_freq=10000
    eval_freq=10000
    eval_episodes=5
    agent_num=2
    tensorboard_log="./logs/"
    model_dir="./models/"
    render_mode="human"  