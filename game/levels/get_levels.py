import os
import sys
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from game.levels.levels import *
from game.levels.level4 import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game.balancing_ball_game import BalancingBallGame

def get_level(level: int, 
              game: 'BalancingBallGame' = None,
              collision_type: dict = None, 
              player_configs: dict = None, 
              platform_configs: dict = None, 
              environment_configs: dict = None,
              level_config_path: str = None,
             ) -> Levels:
    """
    Get the level object based on the level number.
    """

    level_cfg = {}
    # Get the directory of the current script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    level_key = ""
    
    if level <= 2:
        if level_config_path is None:
            level_config_path = os.path.join(dir_path, './level_1_2_default_cfg.json')
        level_key = f"level1_2"
    else:
        if level_config_path is None:
            level_config_path = os.path.join(dir_path, f'./level_{level}_default_cfg.json')
        level_key = f"level{level}"
    
    print(f"Loading level configurations from {level_config_path}...")
    with open(level_config_path, 'r') as f:
        default_configs = json.load(f)
    
    if not player_configs:
        player_configs = default_configs.get("player_configs", [])
    if not collision_type:
        collision_type = default_configs.get("collision_type", {})

    if level_key in default_configs:
        level_cfg = default_configs[level_key]
        if isinstance(platform_configs, list) and len(platform_configs) > 0:
            level_cfg["platform_configs"] = platform_configs
        if not environment_configs:
            environment_configs = level_cfg.get("environment_configs", [])
    else:
        raise ValueError(f"Default config for level {level} not found in {level_config_path}")

    if not player_configs:
        raise ValueError(f"Invalid player_configs: {player_configs}, must be a non-empty list or dict")

    if not environment_configs:
        raise ValueError(f"Invalid environment_configs: {environment_configs}, must be a non-empty list or dict")

    print(f"Using collision_type: {collision_type}")
    print(f"Using player_configs: {player_configs}")
    print(f"Using level_configs: {level_cfg}")

    game.set_windows_size(environment_configs[0].get("window_x"), environment_configs[0].get("window_y"))
    space = game.get_space()
    space.gravity = tuple(environment_configs[0].get("gravity"))
    space.damping = environment_configs[0].get("damping")

    if level == 1:
        return Level1(game=game, collision_type=collision_type, player_configs=player_configs, level_configs=level_cfg)
    elif level == 2:
        return Level2(game=game, collision_type=collision_type, player_configs=player_configs, level_configs=level_cfg)
    elif level == 3:
        return Level3(game=game, collision_type=collision_type, player_configs=player_configs, level_configs=level_cfg)
    elif level == 4:
        return Level4(game=game, collision_type=collision_type, player_configs=player_configs, level_configs=level_cfg)
    else:
        raise ValueError(f"Invalid level number: {level}")