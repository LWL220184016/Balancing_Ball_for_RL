from balancing_ball_game import BalancingBallGame
from gym_env import BalancingBallEnv

def run_standalone_game(render_mode="human", capture_per_second=None, window_x=None, window_y=None, max_step=None, collision_type=None, player_configs=None, platform_configs=None, environment_configs=None, level=None, fps=None):
    """Run the game in standalone mode with visual display"""


    game = BalancingBallGame(
        render_mode = render_mode,
        window_x = window_x,
        window_y = window_y,
        max_step = max_step,
        collision_type = collision_type,
        player_configs = player_configs,
        platform_configs = platform_configs,
        environment_configs = environment_configs,
        level = level,
        fps = fps,
        capture_per_second = capture_per_second,
    )

    game.run_standalone()

def test_gym_env(episodes=3, window_x:int=None, window_y:int=None):
    """Test the OpenAI Gym environment"""
    # from gym_env import BalancingBallEnv
    from RL.levels.level3.config import model_config
    import pygame  # 導入 pygame

    env = BalancingBallEnv(
        render_mode="human",
        model_cfg=model_config,
        window_x=1000,
        window_y=1000
    )

    for episode in range(episodes):
        observation, info = env.reset()
        total_reward = 0
        step = 0
        done = False

        while not done:
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True # 如果點擊關閉按鈕，則結束迴圈

                if done: # 檢查是否需要提前退出
                    break
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

    # # rgb_array_and_human_in_colab
    # run_standalone_game(render_mode="human", 
    #                     window_x=1000, 
    #                     window_y=1000, 
    #                     max_step=30000,
    #                     collision_type=collision_type,
    #                     player_configs=player_configs,
    #                     platform_configs=platform_configs,
    #                     environment_configs=environment_configs,
    #                     level=3, 
    #                     fps=360,
    #                     capture_per_second=None
    #                    )
    
    
    test_gym_env(episodes=1,
                 window_x=1000,
                 window_y=1000
                )