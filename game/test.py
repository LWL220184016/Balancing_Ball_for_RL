from balancing_ball_game import BalancingBallGame
from gym_env import BalancingBallEnv

def run_standalone_game(render_mode="human", capture_per_second=None, window_x=1000, window_y=600, collision_type=None, player_configs=None, platform_configs=None, environment_configs=None, level=2, fps=120):
    """Run the game in standalone mode with visual display"""


    game = BalancingBallGame(
        render_mode = render_mode,
        window_x = window_x,
        window_y = window_y,
        collision_type = collision_type,
        player_configs = player_configs,
        platform_configs = platform_configs,
        environment_configs = environment_configs,
        level = level,
        fps = fps,
        capture_per_second = capture_per_second,
    )

    game.run_standalone()

def test_gym_env(episodes=3):
    """Test the OpenAI Gym environment"""
    # from gym_env import BalancingBallEnv

    fps = 30
    env = BalancingBallEnv(
        render_mode="rgb_array_and_human_in_colab",
        fps=fps,
    )

    for episode in range(episodes):
        observation, info = env.reset()
        total_reward = 0
        step = 0
        done = False

        while not done:
            # Sample a random action (for testing only)
            action = env.action_space.sample()

            # Take step
            observation, reward, terminated, truncated, _ = env.step(action)

            done = terminated or truncated
            total_reward += reward
            step += 1

            # Render
            env.render()

        print(f"Episode {episode+1}: Steps: {step}, Total Reward: {total_reward:.2f}")

    env.close()

if __name__ == "__main__":
    # Example usage:
    collision_type = None
    player_configs = None
    platform_configs = None
    environment_configs = None
    # environment_configs = [
    #             {
    #                 "gravity": [0, 9810],
    #                 "damping": 0.9
    #             }
    #         ]

    # rgb_array_and_human_in_colab
    run_standalone_game(render_mode="human", 
                        window_x=1000, 
                        window_y=1000, 
                        collision_type=collision_type,
                        player_configs=player_configs,
                        platform_configs=platform_configs,
                        environment_configs=environment_configs,
                        level=1, 
                        fps=360,
                        capture_per_second=None
                       )
    # test_gym_env()