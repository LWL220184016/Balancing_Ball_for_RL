import os
import numpy as np
import pygame
import time
import cv2
import argparse

from env import BallBalanceEnv
from ppo_agent import PPOAgent
from run import space, bodies, reset_game, WINDOW_X, WINDOW_Y

def evaluate(model_path, num_episodes=5, render=True):
    """Evaluate a trained model on the game."""
    # Create the environment
    env = BallBalanceEnv(space, bodies, reset_game, window_size=(WINDOW_X, WINDOW_Y), render_mode='rgb_array' if render else None)
    
    # Get environment information
    observation_shape = env.observation_space.shape
    action_space = env.action_space
    
    # Initialize PPO agent
    agent = PPOAgent(observation_shape, action_space)
    
    # Load model
    agent.load(model_path)
    
    # Set up display if rendering
    if render:
        pygame.init()
        screen = pygame.display.set_mode((WINDOW_X, WINDOW_Y))
        clock = pygame.time.Clock()
    
    # Evaluation loop
    episode_rewards = []
    episode_lengths = []
    
    for episode in range(1, num_episodes + 1):
        state, _ = env.reset()
        episode_reward = 0
        steps = 0
        done = False
        truncated = False
        
        while not (done or truncated):
            # Get action from agent
            action = agent.select_action(state, training=False)
            
            # Take action
            next_state, reward, done, truncated, info = env.step(action)
            
            # Update state and counters
            state = next_state
            episode_reward += reward
            steps += 1
            
            # Render if requested
            if render:
                # Process the frame for display
                frame = env.render()
                
                # Convert the frame from RGB to BGR (for pygame display)
                frame = np.flip(frame, axis=2)
                
                # Create a surface from the array
                surf = pygame.surfarray.make_surface(frame)
                
                # Display the frame
                screen.blit(surf, (0, 0))
                pygame.display.flip()
                
                # Control frame rate
                clock.tick(60)
                
                # Check for quit event
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
        
        # Record statistics
        episode_rewards.append(episode_reward)
        episode_lengths.append(steps)
        
        print(f"Episode {episode}/{num_episodes} - "
              f"Reward: {episode_reward:.2f}, Steps: {steps}")
    
    # Print evaluation summary
    avg_reward = np.mean(episode_rewards)
    avg_length = np.mean(episode_lengths)
    print(f"\nEvaluation complete over {num_episodes} episodes:")
    print(f"Average Reward: {avg_reward:.2f}")
    print(f"Average Episode Length: {avg_length:.2f}")
    
    if render:
        pygame.quit()
        
    return avg_reward, avg_length

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='models/best_model.pt', help='Path to model file')
    parser.add_argument('--episodes', type=int, default=5, help='Number of episodes to evaluate')
    parser.add_argument('--no-render', action='store_true', help='Disable rendering')
    args = parser.parse_args()
    
    evaluate(args.model, args.episodes, not args.no_render)
