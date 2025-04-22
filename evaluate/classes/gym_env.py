import gym
import numpy as np
from gym import spaces

from classes.game import BalancingBallGame

class BalancingBallEnv(gym.Env):
    """
    OpenAI Gym environment for the Balancing Ball game
    """
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self, render_mode="rgb_array", difficulty="medium", fps=30):
        super(BalancingBallEnv, self).__init__()

        # Action space: discrete - 0: left, 1: right
        self.action_space = spaces.Discrete(2)

        # Initialize game
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
            fps = fps,
        )

        # Image observation space (RGB)
        self.observation_space = spaces.Box(
            low=0, high=255,
            shape=(self.window_y, self.window_x, 3),
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

        # OpenAI Gym expects (observation, reward, terminated, truncated, info)
        return obs, step_reward, terminated, False, {}

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