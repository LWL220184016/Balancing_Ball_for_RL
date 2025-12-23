from balancing_ball_game import BalancingBallGame

# Example usage:
collision_type = None
player_configs = None
platform_configs = None
environment_configs = None

# rgb_array_and_human_in_colab
game = BalancingBallGame(render_mode="human", 
                            max_episode_step=30000,
                            collision_type=collision_type,
                            player_configs=player_configs,
                            platform_configs=platform_configs,
                            environment_configs=environment_configs,
                            level=4, 
                            fps=360,
                            capture_per_second=None
                        )

game.run_standalone()

