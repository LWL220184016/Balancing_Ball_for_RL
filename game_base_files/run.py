import argparse

from balancing_ball_game import BalancingBallGame

def run_standalone_game(difficulty="medium"):
    """Run the game in standalone mode with visual display"""
    window_x = 1000
    window_y = 600
    platform_shape = "circle"
    platform_length = 200

    game = BalancingBallGame(
        difficulty=difficulty, 
        window_x = window_x, 
        window_y = window_y, 
        platform_shape = platform_shape, 
        platform_length = platform_length, 
        fps = 30, 
    )
    
    game.run_standalone()

def test_gym_env(episodes=3, difficulty="medium"):
    """Test the OpenAI Gym environment"""
    import time
    from gym_env import BalancingBallEnv
    
    fps = 30
    env = BalancingBallEnv(
        render_mode="human", 
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Balancing Ball game')
    parser.add_argument('--mode', type=str, default='gym', 
                        choices=['game', 'gym'],
                        help='Mode to run: standalone game or gym environment test')
    parser.add_argument('--difficulty', type=str, default='medium',
                        choices=['easy', 'medium', 'hard'],
                        help='Game difficulty level')
    args = parser.parse_args()
    
    if args.mode == 'game':
        run_standalone_game(difficulty=args.difficulty)
    else:
        test_gym_env(difficulty=args.difficulty)