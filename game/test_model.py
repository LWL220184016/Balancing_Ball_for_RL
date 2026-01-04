import ray
import gymnasium as gym
import importlib
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
from ray.rllib.policy.policy import PolicySpec
from ray.rllib.algorithms.callbacks import DefaultCallbacks
from ray.rllib.algorithms.algorithm import Algorithm
from game.script.gym_env import BalancingBallEnv


def env_creator(env_config):
    # env_config 是從 AlgorithmConfig 傳進來的字典
    return BalancingBallEnv(
        render_mode=env_config.get("render_mode"),
        model_cfg=env_config.get("model_cfg"),
        train_cfg=env_config.get("train_cfg")
    )
# 註冊環境名稱，必須與訓練時使用的字符串一致
register_env("balancing_ball_v1", env_creator)
# 1. 啟動 Ray (如果尚未啟動)
ray.init()

# 2. 指定 Checkpoint 的路徑
# 注意：路徑通常指向名為 "checkpoint_000xxx" 的文件夾
checkpoint_path1 = "C:/Users/User/ray_results/PPO_2026-01-04_11-35-06/PPO_balancing_ball_v1_5cec0_00000_0_2026-01-04_11-35-06/checkpoint_000039"
checkpoint_path2 = "C:/Users/User/ray_results/PPO_2026-01-03_23-18-35/PPO_balancing_ball_v1_79041_00000_0_2026-01-03_23-18-35/checkpoint_000009"

# 3. 從 Checkpoint 恢復算法實例
# 不需要重新定義 config，它會自動從 checkpoint 中讀取
algo1 = Algorithm.from_checkpoint(checkpoint_path1)
policy_ids1 = algo1.get_policy()
print(f"當前可用的 Policies: {policy_ids1}")

algo2 = Algorithm.from_checkpoint(checkpoint_path2)
policy_ids2 = algo2.get_policy()
print(f"當前可用的 Policies: {policy_ids2}")

level = 4
module_path = f"RL.levels.level{level}.model1.config"

try:
    imported_module = importlib.import_module(module_path)
    train_config = imported_module.train_config
    model_config = imported_module.model_config
except ImportError as e:
    print(f"錯誤：找不到 Level {level} 的配置文件或是路徑錯誤。")
    print(f"嘗試路徑: {module_path}")
    raise e
except AttributeError as e:
    print(f"錯誤：在 Level {level} 的 config.py 中找不到 model_config 或 train_config。")
    raise e

env = BalancingBallEnv(render_mode="human", model_cfg=model_config, train_cfg=train_config)
obs_dict, info = env.reset()

done = {"__all__": False}
total_rewards = {}

while not done["__all__"]:
    action_dict = {}
    
    # 為環境中的每個 Agent 計算動作
    for agent_id, obs in obs_dict.items():
        # --- Self-play 測試策略選擇邏輯 ---
        # 假設 agent_0 是你要測試的最新模型，agent_1 是對手
        if agent_id == "RL_player0":
            policy_id = "main"  # 使用當前最強的 Policy
        else:
            policy_id = "main_opponent" # 使用之前的舊版本作為對手，或者 "random"
            
        # 計算動作
        action = algo1.compute_single_action(
            observation=obs,
            policy_id=policy_id,
            explore=False # 測試時關閉隨機性
        )
        action_dict[agent_id] = action
        
        # if agent_id == "RL_player0":
        #     action = algo1.compute_single_action(
        #         observation=obs,
        #         policy_id="main",
        #         explore=False # 測試時關閉隨機性
        #     )
        #     action_dict[agent_id] = action
        # else:
        #     action = algo2.compute_single_action(
        #         observation=obs,
        #         policy_id="main",
        #         explore=False # 測試時關閉隨機性
        #     )
        #     action_dict[agent_id] = action
            
        # 計算動作

    # 執行動作
    print(action_dict)
    obs_dict, reward_dict, terminated, truncated, info = env.step(action_dict)
    
    # 累積獎勵
    for agent_id, r in reward_dict.items():
        total_rewards[agent_id] = total_rewards.get(agent_id, 0) + r
    
    # 判斷是否結束
    done = terminated
    done.update(truncated)
    
    env.render()
    print("test_model: ", terminated)
    for key, value in terminated.items():
        if value:
            env.reset()

print(f"測試結束，各玩家獎勵: {total_rewards}")
