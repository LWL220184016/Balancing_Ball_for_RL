from script.balancing_ball_game import BalancingBallGame

# Example usage:
collision_type = None
player_configs = None
platform_configs = None
environment_configs = None

# game = BalancingBallGame(render_mode="headless", 
game = BalancingBallGame(render_mode="human", 
                            max_episode_step=30000,
                            collision_type=collision_type,
                            player_configs=player_configs,
                            platform_configs=platform_configs,
                            environment_configs=environment_configs,
                            level=4, 
                            sub_level=0,
                            capture_per_second=None
                        )

game.run_standalone("Human_player1")

