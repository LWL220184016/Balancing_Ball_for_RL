import torch

from stable_baselines3.common.policies import ActorCriticPolicy, ActorCriticCnnPolicy  # MLP policy instead of CNN

class model_config:
    model_obs_type="game_screen",

    model_param={
        # ActorCriticCnnPolicyif for game_screen, ActorCriticPolicy for state base
        "policy": ActorCriticCnnPolicy,  

        "learning_rate": 0.0001,
        "n_steps": 2048,
        "batch_size": 64,
        "n_epochs": 10,
        "gamma": 0.995,
        "clip_range": 0.15,
        "gae_lambda": 0.98,
        "ent_coef": 0.02,
        "vf_coef": 0.5,
        "max_grad_norm": 0.5,
        "policy_kwargs": {
                "features_extractor_kwargs": {"features_dim": 512},
                "net_arch": [512, 512, 256],  # 增加網絡深度以處理複雜策略
                "activation_fn": torch.nn.ReLU,
            },
        "verbose": 1,
    }

class train_config:
    total_timesteps=1000000,
    save_freq=10000,
    eval_freq=10000,
    eval_episodes=5,
    tensorboard_log="./logs/",
    model_dir="./models/",