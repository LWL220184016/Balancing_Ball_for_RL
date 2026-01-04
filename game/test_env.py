import importlib
import sys
import os

from script.gym_env import BalancingBallEnv

current_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

level = 4
episode_num = 3
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

env = BalancingBallEnv(render_mode="headless", model_cfg=model_config, train_cfg=train_config)

terminateds = {}
terminateds["__all__"] = False
for n in range(episode_num):
    print(f"episode_num: {n+1}")
    while not terminateds["__all__"]:
        action = {'RL_player0': {'Move_topdown_viewing_angle': (0, 0), 'Shoot': 1}}
        mixed_obs, step_rewards, terminateds, truncateds, info = env.step(action)

    terminateds["__all__"] = False
    env.reset()