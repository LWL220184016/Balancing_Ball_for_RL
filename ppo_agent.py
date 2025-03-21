import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.distributions import Categorical
from collections import deque

class CNN(nn.Module):
    def __init__(self, observation_shape, hidden_size=256):
        super(CNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(observation_shape[2], 32, kernel_size=8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU()
        )
        
        # Calculate output size of CNN
        self.cnn_output_dim = self._get_conv_output(observation_shape)
        
        self.fc = nn.Sequential(
            nn.Linear(self.cnn_output_dim, hidden_size),
            nn.ReLU()
        )
        
    def _get_conv_output(self, shape):
        x = torch.zeros(1, shape[2], shape[0], shape[1])
        x = self.features(x)
        return int(np.prod(x.shape))
    
    def forward(self, x):
        # Reshape to (batch_size, channels, height, width)
        x = x.permute(0, 3, 1, 2)
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

class ActorCritic(nn.Module):
    def __init__(self, observation_shape, num_actions, hidden_size=256):
        super(ActorCritic, self).__init__()
        
        # Feature extraction part
        self.cnn = CNN(observation_shape, hidden_size)
        
        # Actor (policy) head
        self.actor = nn.Sequential(
            nn.Linear(hidden_size, num_actions),
            nn.Softmax(dim=-1)
        )
        
        # Critic (value) head
        self.critic = nn.Sequential(
            nn.Linear(hidden_size, 1)
        )
    
    def forward(self, x):
        if isinstance(x, np.ndarray):
            x = torch.FloatTensor(x)
        
        features = self.cnn(x)
        action_probs = self.actor(features)
        value = self.critic(features)
        
        return action_probs, value

class PPOAgent:
    def __init__(self, observation_shape, action_space, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        self.observation_shape = observation_shape
        self.num_actions = action_space.n
        
        self.actor_critic = ActorCritic(observation_shape, self.num_actions).to(device)
        self.optimizer = optim.Adam(self.actor_critic.parameters(), lr=3e-4)
        
        # PPO hyperparameters
        self.gamma = 0.99
        self.gae_lambda = 0.95
        self.clip_epsilon = 0.2
        self.value_coef = 0.5
        self.entropy_coef = 0.01
        self.max_grad_norm = 0.5
        self.ppo_epochs = 10
        self.mini_batch_size = 64
        
        # Memory
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.dones = []
        
    def select_action(self, state, training=True):
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # Get action probabilities and value
        with torch.no_grad():
            action_probs, value = self.actor_critic(state)
        
        # Create categorical distribution and sample
        dist = Categorical(action_probs)
        
        if training:
            action = dist.sample()
            log_prob = dist.log_prob(action)
            
            # Convert to numpy/python types for storage
            action = action.cpu().numpy()[0]
            log_prob = log_prob.cpu().numpy()[0]
            value = value.cpu().numpy()[0]
            
            return action, log_prob, value
        else:
            # During evaluation, take the most probable action
            action = torch.argmax(action_probs, dim=-1).cpu().numpy()[0]
            return action
        
    def store_transition(self, state, action, reward, log_prob, value, done):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.dones.append(done)
        
    def clear_memory(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.dones = []
        
    def compute_gae(self, next_value, rewards, values, dones):
        advantages = []
        gae = 0
        
        for i in reversed(range(len(rewards))):
            if i == len(rewards) - 1:
                delta = rewards[i] + self.gamma * next_value * (1 - dones[i]) - values[i]
            else:
                delta = rewards[i] + self.gamma * values[i+1] * (1 - dones[i]) - values[i]
                
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[i]) * gae
            advantages.insert(0, gae)
            
        return advantages
    
    def update(self, next_value=0):
        # Convert lists to tensors
        states = torch.FloatTensor(np.array(self.states)).to(self.device)
        actions = torch.LongTensor(np.array(self.actions)).to(self.device)
        old_log_probs = torch.FloatTensor(np.array(self.log_probs)).to(self.device)
        rewards = np.array(self.rewards)
        values = np.array(self.values)
        dones = np.array(self.dones)
        
        # Compute advantages and returns
        advantages = self.compute_gae(next_value, rewards, values, dones)
        advantages = torch.FloatTensor(advantages).to(self.device)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Compute returns
        returns = advantages + torch.FloatTensor(values).to(self.device)
        
        # PPO update
        total_loss = 0
        actor_loss = 0
        critic_loss = 0
        entropy = 0
        
        for _ in range(self.ppo_epochs):
            # Create mini-batches
            batch_size = states.size(0)
            indices = torch.randperm(batch_size)
            
            for start_idx in range(0, batch_size, self.mini_batch_size):
                end_idx = min(start_idx + self.mini_batch_size, batch_size)
                batch_indices = indices[start_idx:end_idx]
                
                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]
                
                # Forward pass
                action_probs, values = self.actor_critic(batch_states)
                dist = Categorical(action_probs)
                
                # Get new log probs
                new_log_probs = dist.log_prob(batch_actions)
                
                # Calculate ratio
                ratio = torch.exp(new_log_probs - batch_old_log_probs)
                
                # Clipped surrogate objective
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon) * batch_advantages
                
                # Calculate losses
                a_loss = -torch.min(surr1, surr2).mean()
                c_loss = 0.5 * ((values.squeeze() - batch_returns) ** 2).mean()
                e_loss = -dist.entropy().mean()
                
                loss = a_loss + self.value_coef * c_loss + self.entropy_coef * e_loss
                
                # Update statistics
                actor_loss += a_loss.item()
                critic_loss += c_loss.item()
                entropy += e_loss.item()
                total_loss += loss.item()
                
                # Update network
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.actor_critic.parameters(), self.max_grad_norm)
                self.optimizer.step()
                
        # Average losses
        epochs = self.ppo_epochs * (len(self.states) // self.mini_batch_size + 1)
        actor_loss /= epochs
        critic_loss /= epochs
        entropy /= epochs
        total_loss /= epochs
        
        # Clear memory
        self.clear_memory()
        
        return {
            "total_loss": total_loss,
            "actor_loss": actor_loss,
            "critic_loss": critic_loss,
            "entropy": entropy
        }
        
    def save(self, path):
        torch.save({
            'model_state_dict': self.actor_critic.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict()
        }, path)
        
    def load(self, path):
        checkpoint = torch.load(path)
        self.actor_critic.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
