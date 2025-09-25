from balancing_ball_game import BalancingBallGame
from gym_env import BalancingBallEnv

def run_standalone_game(render_mode="human", difficulty="medium", capture_per_second=None, window_x=1000, window_y=600, player_configs=None, platform_configs=None, environment_configs=None, level=2):
    """Run the game in standalone mode with visual display"""


    game = BalancingBallGame(
        render_mode = render_mode,
        difficulty = difficulty,
        window_x = window_x,
        window_y = window_y,
        player_configs = player_configs,
        platform_configs = platform_configs,
        environment_configs = environment_configs,
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

player_configs = [
            {
                "ball_color": [
                    255, 
                    213, 
                    79
                ],
                "default_player_position": [
                    0.4,
                    0.2
                ]
            },
            {
                "ball_color": [
                    194,
                    238,
                    84
                ],
                "default_player_position": [
                    0.6,
                    0.2
                ]
            }
        ]

platform_configs = [
            {
                "platform_shape_type": "rectangle",
                "platform_proportion": 0.8,
                "platform_position": [
                    0.5,
                    0.67
                ]
            },
            {
                "platform_shape_type": "circle",
                "platform_proportion": 0.1,
                "platform_position": [
                    0.25,
                    0.4
                ]
            }
        ]
environment_configs = [
            {
                "gravity": [0, 9810],
                "damping": 0.9
            }
        ]

# rgb_array_and_human_in_colab
run_standalone_game(render_mode="human", 
                    difficulty="medium", 
                    window_x=1000, 
                    window_y=600, 
                    player_configs=player_configs,
                    platform_configs=platform_configs,
                    environment_configs=environment_configs,
                    level=3, 
                    capture_per_second=None
                    )
# test_gym_env(difficulty="medium")