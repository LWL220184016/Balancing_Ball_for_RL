from balancing_ball_game import BalancingBallGame
from gym_env import BalancingBallEnv

def run_standalone_game(render_mode="human", difficulty="medium", capture_per_second=None, window_x=1000, window_y=600, level=2):
    """Run the game in standalone mode with visual display"""

    platform_shape = "circle"
    platform_proportion = 0.333

    game = BalancingBallGame(
        render_mode = render_mode,
        difficulty = difficulty,
        window_x = window_x,
        window_y = window_y,
        platform_shape = platform_shape,
        platform_proportion = platform_proportion,
        level = level,
        fps = 120,
        capture_per_second = capture_per_second,
    )

    game.run_standalone()

def test_gym_env(episodes=3, difficulty="medium"):
    """Test the OpenAI Gym environment"""
    # from gym_env import BalancingBallEnv

    fps = 30
    env = BalancingBallEnv(
        render_mode="rgb_array_and_human_in_colab",
        difficulty=difficulty,
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

# rgb_array_and_human_in_colab
run_standalone_game(render_mode="human", 
                    difficulty="medium", 
                    window_x=1000, 
                    window_y=600, 
                    level=3, 
                    capture_per_second = None
                    )
# test_gym_env(difficulty="medium")