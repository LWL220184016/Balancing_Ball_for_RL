import gymnasium as gym
import numpy as np
from gymnasium import spaces

from classes.balancing_ball_game import BalancingBallGame

class BalancingBallEnv(gym.Env):
    """
    Gymnasium environment for the Balancing Ball game
    """
    metadata = {'render_modes': ['human', 'rgb_array']}

    def __init__(self, render_mode="rgb_array", difficulty="medium", fps=30):
        super(BalancingBallEnv, self).__init__()

        # Action space: discrete - 0: left, 1: right
        self.action_space = spaces.Discrete(2)

        # Initialize game
        self.window_x = 1000
        self.window_y = 600
        self.platform_shape = "circle"
        self.platform_length = 200

        self.stack_size = 3  # Number of frames to stack
        self.observation_stack = []  # Initialize the stack
        self.render_mode = render_mode

        self.game = BalancingBallGame(
            render_mode=render_mode,
            sound_enabled=(render_mode == "human"),
            difficulty=difficulty,
            window_x = self.window_x,
            window_y = self.window_y,
            platform_shape = self.platform_shape,
            platform_length = self.platform_length,
            fps = fps,
        )

        # Image observation space (RGB) with stacked frames
        self.observation_space = spaces.Box(
            low=0, high=255,
            shape=(self.window_y, self.window_x, 3 * self.stack_size),  # For stacked frames
            dtype=np.uint8
        )

        # Platform_length /= 2 when for calculate the distance to the
        # center of game window coordinates. The closer you are, the higher the reward.
        self.platform_length = (self.platform_length / 2) - 5

        # When the ball is to be 10 points away from the center coordinates,
        # it should be 1 - ((self.platform_length - 10) * self.x_axis_max_reward_rate)
        self.x_axis_max_reward_rate = 0.5 / self.platform_length

    def step(self, action):
        """Take a step in the environment"""
        # Convert from discrete action to the game's expected format
        action_value = -1.0 if action == 0 else 1.0

        # Take step in the game
        # todo
        # 修改代码变成模型执行一次动作然后在接下来的一定禎数持续该动作，同时收集并且堆叠祯然后给模型预测下一次动作
        # 比如一次循环为6祯，那麼模型一次动作将持续六祯，同时堆叠该6祯给模型预测下一次动作
        obs, step_reward, terminated = self.game.step(action_value)

        # Stack the frames
        self.observation_stack.append(obs)
        if len(self.observation_stack) > self.stack_size:
            self.observation_stack.pop(0)  # Remove the oldest frame

        # If the stack isn't full yet, pad it with the current frame
        while len(self.observation_stack) < self.stack_size:
            self.observation_stack.insert(0, obs)  # Pad with current frame at the beginning

        stacked_obs = np.concatenate(self.observation_stack, axis=-1)

        # Gymnasium expects (observation, reward, terminated, truncated, info)
        return stacked_obs, step_reward, terminated, False, {}

    def reset(self, seed=None, options=None):
        """Reset the environment"""
        super().reset(seed=seed)  # This properly seeds the environment in Gymnasium

        observation = self.game.reset()

        # Reset the observation stack
        self.observation_stack = []

        # Fill the stack with the initial observation
        for _ in range(self.stack_size):
            self.observation_stack.append(observation)

        # Create stacked observation
        stacked_obs = np.concatenate(self.observation_stack, axis=-1)

        info = {}
        return stacked_obs, info

    def render(self):
        """Render the environment"""
        return self.game.render()

    def close(self):
        """Clean up resources"""
        self.game.close()