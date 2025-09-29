import os
import json
from levels.levels import *

def get_level(level: int, space, collision_type=None, player_configs=None, platform_configs=None, environment_configs=None):
    """
    Get the level object based on the level number.
    """
    level_cfg = {}
    if not collision_type or not player_configs or not platform_configs or not environment_configs:
        # Get the directory of the current script
        print("Loading default level configurations...")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        level_key = ""
        
        if level <= 2:
            config_path = os.path.join(dir_path, './level_1_2_default_cfg.json')
            level_key = f"level1_2"
        else:
            config_path = os.path.join(dir_path, './level_3_default_cfg.json')
            level_key = f"level{level}"
        with open(config_path, 'r') as f:
            default_configs = json.load(f)
        
        if not player_configs:
            player_configs = default_configs.get("player_configs", [])
        if not collision_type:
            collision_type = default_configs.get("collision_type", {})

        if level_key in default_configs:
            level_cfg = default_configs[level_key]
            if not platform_configs:
                platform_configs = level_cfg.get("platform_configs", [])
            if not environment_configs:
                environment_configs = level_cfg.get("environment_configs", [])
        else:
            raise ValueError(f"Default config for level {level} not found in {config_path}")

    if not player_configs:
        raise ValueError(f"Invalid player_configs: {player_configs}, must be a non-empty list or dict")

    if not environment_configs:
        raise ValueError(f"Invalid environment_configs: {environment_configs}, must be a non-empty list or dict")

    print(f"Using collision_type: {collision_type}")
    print(f"Using player_configs: {player_configs}")
    print(f"Using platform_configs: {platform_configs}")
    print(f"Using environment_configs: {environment_configs}")

    space.gravity = tuple(environment_configs[0].get("gravity"))
    space.damping = environment_configs[0].get("damping")

    if level == 1:
        return Level1(space, collision_type, player_configs, platform_configs, level_cfg)
    elif level == 2:
        return Level2(space, collision_type, player_configs, platform_configs, level_cfg)
    elif level == 3:
        return Level3(space, collision_type, player_configs, platform_configs, level_cfg)
    else:
        raise ValueError(f"Invalid level number: {level}")