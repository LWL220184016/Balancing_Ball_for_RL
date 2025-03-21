import os
import numpy as np
import torch
import time
import matplotlib.pyplot as plt
from collections import deque

import pymunk

from env import BallBalanceEnv
from ppo_agent import PPOAgent
from run import space, bodies, reset_game, WINDOW_X, WINDOW_Y

def plot_learning_curve(x, scores, figure_file='learning_curve.png'):
    """Plot learning curve for the agent."""
    running_avg = np.zeros(len(scores))
    for i in range(len(running_avg)):
        running_avg[i] = np.mean(scores[max(0, i-100):(i+1)])
    
    plt.figure(figsize=(12, 6))
    plt.plot(x, scores, color='skyblue', label='Scores')
    plt.plot(x, running_avg, color='blue', label='Running Avg')
    plt.title('Learning Curve')
    plt.xlabel('Episodes')
    plt.ylabel('Score')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(figure_file)
    
def train():
    # Create directories for saving
    os.makedirs('models', exist_ok=True)
    os.makedirs('plots', exist_ok=True)
    
    # Create the environment
    env = BallBalanceEnv(space, bodies, reset_game, window_size=(WINDOW_X, WINDOW_Y))
    
    # Get environment information
    observation_shape = env.observation_space.shape
    action_space = env.action_space
    
    # Initialize PPO agent
    agent = PPOAgent(observation_shape, action_space)
    
    # Training parameters
    num_episodes = 1000
    max_steps_per_episode = 1000
    update_frequency = 2048  # Number of steps before updating the policy
    
    # Tracking metrics
    episode_rewards = []
    step_counter = 0
    best_avg_reward = -float('inf')
    
    # For tracking progress
    scores = []
    avg_scores = []
    steps_array = []
    
    # Timer
    start_time = time.time()
    
    # Moving average window
    rewards_window = deque(maxlen=100)
    
    for episode in range(1, num_episodes + 1):
        state, _ = env.reset()
        episode_reward = 0
        done = False
        truncated = False
        
        for step in range(max_steps_per_episode):
            # Select action
            action, log_prob, value = agent.select_action(state)
            
            # Take action
            next_state, reward, done, truncated, info = env.step(action)
            
            # Store transition
            agent.store_transition(state, action, reward, log_prob, value, done)
            
            # Update state and counters
            state = next_state
            episode_reward += reward
            step_counter += 1
            
            # Update policy if enough steps have been accumulated
            if step_counter % update_frequency == 0:
                # Get last value (for bootstrapping)
                with torch.no_grad():
                    _, last_value = agent.actor_critic(
                        torch.FloatTensor(next_state).unsqueeze(0).to(agent.device)
                    )
                    last_value = last_value.cpu().numpy()[0]
                
                # Update policy
                loss_info = agent.update(last_value)
                
                print(f"Update at step {step_counter}, Actor Loss: {loss_info['actor_loss']:.4f}, "
                      f"Critic Loss: {loss_info['critic_loss']:.4f}")
            
            if done or truncated:
                break
        
        # Track episode rewards
        rewards_window.append(episode_reward)
        episode_rewards.append(episode_reward)
        scores.append(episode_reward)
        steps_array.append(episode)
        avg_score = np.mean(rewards_window)
        avg_scores.append(avg_score)
        
        # Print progress
        elapsed_time = time.time() - start_time
        print(f"Episode {episode}/{num_episodes} | "
              f"Steps: {step+1} | "
              f"Reward: {episode_reward:.2f} | "
              f"Avg Reward: {avg_score:.2f} | "
              f"Time: {elapsed_time:.2f}s")
        
        # Save best model
        if avg_score > best_avg_reward and episode > 50:
            best_avg_reward = avg_score
            agent.save(f"models/best_model.pt")
            print(f"New best model saved with average reward: {best_avg_reward:.2f}")
            
        # Save checkpoint every 50 episodes
        if episode % 50 == 0:
            agent.save(f"models/checkpoint_{episode}.pt")
            plot_learning_curve(steps_array, scores, figure_file=f'plots/learning_curve_{episode}.png')
    
    # Save final model
    agent.save("models/final_model.pt")
    
    # Plot learning curve
    plot_learning_curve(steps_array, scores, figure_file='plots/final_learning_curve.png')
    
    return agent

if __name__ == "__main__":
    trained_agent = train()
