import importlib
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

import ray
import random       
import numpy as np  
import torch        

from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
from ray.rllib.policy.policy import PolicySpec
from ray.rllib.algorithms.callbacks import DefaultCallbacks
from game.script.gym_env import BalancingBallEnv


# 假設你的環境類在 environment.py 中
# from your_module import BalancingBallEnv

def env_creator(env_config):
    # env_config 是從 AlgorithmConfig 傳進來的字典
    return BalancingBallEnv(
        render_mode=env_config.get("render_mode"),
        model_cfg=env_config.get("model_cfg"),
        train_cfg=env_config.get("train_cfg")
    )

def set_global_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# 註冊環境
register_env("balancing_ball_v1", env_creator)

def run_training(level: int, checkpoint_path: str = None):
    ray.init()

    module_path = f"RL.levels.level{level}.model1.config"

    try:
        imported_module = importlib.import_module(module_path)
        train_config = imported_module.train_config
        model_config = imported_module.model_config
        set_global_seed(train_config.seed)
    except ImportError as e:
        print(f"錯誤：找不到 Level {level} 的配置文件或是路徑錯誤。")
        print(f"嘗試路徑: {module_path}")
        raise e
    except AttributeError as e:
        print(f"錯誤：在 Level {level} 的 config.py 中找不到 model_config 或 train_config。")
        raise e

    # 1. 定義 Policy
    # 這裡我們定義兩個 policy，它們共用同樣的 observation 和 action space
    # 假設 agent_id 是 RL_player0 和 RL_player1
    
    # 這裡只是占位，你需要根據你的實例獲取 space
    # 建議先實例化一個環境來抓取 space 屬性
    test_env = BalancingBallEnv(render_mode="headless", model_cfg=model_config, train_cfg=train_config)
    obs_space = test_env.observation_space
    act_space = test_env.action_space
    agent_list = test_env.agent_ids
    test_env.close()

    def policy_mapping_fn(agent_id, episode, worker, **kwargs):
        # 決定哪個 agent 使用哪個 policy
        # 在 1v1 中，通常 player0 是 main，player1 是 opponent
        if agent_id == agent_list[0]:
            return "main"
        else:
            return "main_opponent"

    # 2. 配置演算法
    policies = {
        "main": PolicySpec(
            observation_space=obs_space[agent_list[0]],
            action_space=act_space[agent_list[0]],
        ),
    }
    if len(agent_list) > 1:
        policies["main_opponent"] = PolicySpec(
            observation_space=obs_space[agent_list[1]],
            action_space=act_space[agent_list[1]],
        )
    config = (
        PPOConfig()
        .environment(
            env="balancing_ball_v1",
            env_config={
                "model_cfg": model_config, 
                "train_cfg": train_config,
                "render_mode": "headless"
            }
        )
        .api_stack(
            enable_rl_module_and_learner=False,
            enable_env_runner_and_connector_v2=False,
        )
        .training(
            model={
                "conv_filters": [
                    [16, [8, 8], 4],   # 160x160 -> 40x40 (160/4=40)
                    [32, [4, 4], 2],   # 40x40 -> 20x20  (40/2=20)
                    [64, [5, 5], 5],   # 20x20 -> 4x4    (20/5=4)
                    [256, [4, 4], 1],  # 4x4 -> 1x1 (這裡將 4x4 的區域捲積成 1x1，輸出 256 個通道)
                ],
                "post_fcnet_hiddens": [512], # 現在 CNN 輸出是 256，對接這裡的 256
                "post_fcnet_activation": "relu",

                "fcnet_hiddens": [256],    
                "vf_share_layers": True,   # 強制共享層，防止輸入維度計算錯誤
                "use_lstm": True, 
                "lstm_cell_size": 256,      # LSTM 隱藏層大小
                "max_seq_len": 20,          # 訓練時展開的時間步長 (預設通常是 20)
            },
            train_batch_size=4000, 
        )
        .update_from_dict({
            "sgd_minibatch_size": 128,
        })
        .framework("torch")  # 或 "tf2"
        .env_runners(
            num_env_runners=4,       # 對應原本的 num_env_runners
            num_envs_per_env_runner=2,       # 對應原本的 num_envs_per_env_runner
            rollout_fragment_length=250, # 顯式設置，避免自動計算出現奇異值
            create_env_on_local_worker=False, 
        )
        .multi_agent(
            policies=policies,
            policy_mapping_fn=policy_mapping_fn,
            policies_to_train=["main"], # 重要：只訓練 main，對手是固定的
        )
        .resources(num_gpus=1) # 如果有 GPU 設置為 1
        .checkpointing(
            export_native_model_files=True, # 導出模型文件
        )
        
    )

    # 3. 設置 Self-Play Callback (關鍵)
    # 用於定期將 main 的權重複製給 main_opponent
    class SelfPlayCallback(DefaultCallbacks):
        def __init__(self):
            super().__init__()
            self.win_rate_threshold = 0.6 # 勝率超過 0.6 就更新對手

        def on_train_result(self, *, algorithm, result, **kwargs):
            # 這裡可以根據自定義的 win_rate 決定是否更新
            # result['hist_stats'] 裡可以拿到你的 winner info
            
            # 簡單範例：每隔一段時間強制更新
            if algorithm.iteration % 5 == 0:
                print(f"Updating opponent policy at iteration {algorithm.iteration}")
                main_weights = algorithm.get_policy("main").get_weights()
                algorithm.get_policy("main_opponent").set_weights(main_weights)

    # 只有在多人模式下，才掛載 SelfPlayCallback
    if len(agent_list) > 1:
        config.callbacks(SelfPlayCallback)


    # 4. 開始訓練
    stop = {"training_iteration": 400}
    
    print("準備開始訓練...")
    if checkpoint_path:
        print(f"將從 Checkpoint 恢復訓練: {checkpoint_path}")
    else:
        print("將開始新的訓練 (從頭開始)")

    tune.run(
        "PPO", 
        config=config.to_dict(), 
        stop=stop,
        checkpoint_freq=10,             
        checkpoint_at_end=True,         
        # storage_path="./ray_results", 指定存檔路徑
        restore=checkpoint_path  
    )

if __name__ == "__main__":
    level = 4
    
    ckpt = None  # 或者填入字串路徑: "/path/to/your/checkpoint_000010"
    # ckpt = "C:/Users/User/ray_results/PPO_2026-01-08_23-00-51/PPO_balancing_ball_v1_d2d9e_00000_0_2026-01-08_23-00-51/checkpoint_000027"

    if len(sys.argv) > 1:
        ckpt = sys.argv[1]

    run_training(level=level, checkpoint_path=ckpt)


