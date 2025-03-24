import gym
import numpy as np
from gym import spaces

from balancing_ball_game import BalancingBallGame

class BalancingBallEnv(gym.Env):
    """
    OpenAI Gym environment for the Balancing Ball game
    """
    metadata = {'render.modes': ['human', 'rgb_array']}
    
    def __init__(self, render_mode="rgb_array", difficulty="medium"):
        super(BalancingBallEnv, self).__init__()
        
        # Action space: platform movement (-1.0 to 1.0)
        self.action_space = spaces.Box(
            low=-1.0, 
            high=1.0, 
            shape=(1,), 
            dtype=np.float32
        )
        
        # Observation space: [ball_x, ball_y, ball_vx, ball_vy, platform_angle, platform_angular_velocity]
        self.observation_space = spaces.Box(
            low=np.array([0, 0, -1, -1, 0, -1], dtype=np.float32),
            high=np.array([1, 1, 1, 1, 1, 1], dtype=np.float32),
            dtype=np.float32
        )
        
        # Create the game instance
        self.window_x = 1000
        self.window_y = 600
        self.platform_shape = "circle"
        self.platform_length = 200

        self.game = BalancingBallGame(
            render_mode=render_mode, 
            sound_enabled=(render_mode == "human"), 
            difficulty=difficulty, 
            window_x = self.window_x, 
            window_y = self.window_y, 
            platform_shape = self.platform_shape, 
            platform_length = self.platform_length, 
            fps = 30, 
        )
        # Platform_length /= 2 when for calculate the distance to the 
        # center of game window coordinates. The closer you are, the higher the reward.
        self.platform_length = (self.platform_length / 2) - 5

        # When the ball is to be 10 points away from the center coordinates, 
        # it should be 1 - ((self.platform_length - 10) * self.x_axis_max_reward_rate)
        self.x_axis_max_reward_rate = 0.5 / self.platform_length
    
    def step(self, action):
        """Take a step in the environment"""
        # Convert from Box action to the game's expected format
        action_value = float(action[0]) if hasattr(action, "__len__") else float(action)
        
        # Take step in the game
        obs, step, ball_x, done = self.game.step(action_value)

        if step < 2000:
            step *= 0.01
        elif step < 5000:
            step *= 0.03
        else:
            step *= 0.05
        x_axis_reward_rate = 1 - ((self.platform_length - ball_x) * self.x_axis_max_reward_rate)
        reward = step * x_axis_reward_rate
        
        # OpenAI Gym expects a different format for info
        return obs, reward, done, False
    
    def reset(self, seed=None, options=None):
        """Reset the environment"""
        if seed is not None:
            np.random.seed(seed)
            
        observation = self.game.reset()
        info = {}
        return observation, info
    
    def render(self, mode='human'):
        """Render the environment"""
        return self.game.render()
    
    def close(self):
        """Clean up resources"""
        self.game.close()