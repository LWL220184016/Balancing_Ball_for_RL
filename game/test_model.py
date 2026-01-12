import ray
import gymnasium as gym
import importlib
import sys
import os
import collections # 用於檢查是否為序列

current_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

import ray
import numpy as np
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
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

# checkpoint_path1 = "C:/Users/User/ray_results/PPO_2026-01-08_23-00-51/PPO_balancing_ball_v1_d2d9e_00000_0_2026-01-08_23-00-51/checkpoint_000023"
checkpoint_path1 = "C:/Users/User/ray_results/PPO_2026-01-10_13-46-01/PPO_balancing_ball_v1_a5589_00000_0_2026-01-10_13-46-01/checkpoint_000012"
checkpoint_path2 = "C:/Users/User/ray_results/PPO_2026-01-04_19-19-59/PPO_balancing_ball_v1_4e70b_00000_0_2026-01-04_19-19-59/checkpoint_000024"

algo1 = Algorithm.from_checkpoint(checkpoint_path1)
policy_ids1 = algo1.get_policy()
print(f"當前可用的 Policies: {policy_ids1}")

try:
    algo2 = Algorithm.from_checkpoint(checkpoint_path2)
    policy_ids2 = algo2.get_policy()
    print(f"當前可用的 Policies: {policy_ids2}")
except ValueError:
    print("無法從 checkpoint2 載入 Algorithm，請確認 checkpoint 是否正確且完整。可能是已經被刪除或損壞。")
    
saved_config = algo1.get_config()
saved_env_config = saved_config.env_config 
print("訓練時使用的參數:", saved_config)
train_config = saved_env_config.get("train_cfg")
model_config = saved_env_config.get("model_cfg")
env = BalancingBallEnv(render_mode="human", model_cfg=model_config, train_cfg=train_config)
obs_dict, info = env.reset()

done = {"__all__": False}
total_rewards = {}

# 建立一個字典來儲存每個 Agent 的 LSTM 狀態
agent_states = {} 

while not done["__all__"]:
    action_dict = {}
    
    for agent_id, obs in obs_dict.items():
        # 決定 Policy ID
        if agent_id == "RL_player0":
            policy_id = "main"
        else:
            policy_id = "main_opponent" # 確保此 Policy ID 存在於 checkpoint 中，否則會報錯
            
        # 如果該 Agent 還沒有狀態，從 Policy 獲取初始狀態
        if agent_id not in agent_states:
            # 獲取對應 policy 的初始狀態 (通常是全0的 list)
            policy = algo1.get_policy(policy_id)
            if policy is None:
                # Fallback 如果找不到 main_opponent，使用 default_policy
                policy = algo1.get_policy("default_policy") 
            agent_states[agent_id] = policy.get_initial_state()

        # 計算動作，並傳入 state
        # compute_single_action 返回 tuple: (action, state_out, extra_info)
        action, state_out, _ = algo1.compute_single_action(
            observation=obs,
            state=agent_states[agent_id],  # <--- 關鍵：傳入當前 LSTM 狀態
            policy_id=policy_id,
            explore=False
        )
        
        # 更新狀態供下一步使用
        agent_states[agent_id] = state_out
        action_dict[agent_id] = action

    # 執行動作
    # print(action_dict)
    obs_dict, reward_dict, terminated, truncated, info = env.step(action_dict)
    for agent_id, r in reward_dict.items():
        total_rewards[agent_id] = total_rewards.get(agent_id, 0) + r

        if "bot" not in agent_id:
            obs = obs_dict[agent_id]["state"]
            print(f"agent_id: {agent_id}, obs_dict: {obs}, reward: {r}")
    
    done = terminated
    done.update(terminated)
    
    env.render()
    
    # 如果某個 Agent 結束了 (Terminated/Truncated)，需要重置它的狀態
    for agent_id, is_done in done.items():
        if is_done and agent_id != "__all__":
            if agent_id in agent_states:
                # 刪除舊狀態，下次迴圈會重新獲取初始狀態
                del agent_states[agent_id]
            
    if done.get("__all__", False):
        print(f"Episode 結束，獎勵: {total_rewards}")

print(f"測試結束，各玩家獎勵: {total_rewards}")