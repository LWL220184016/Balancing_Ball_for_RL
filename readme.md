# Update
V1:
V2:
V3:

V4:
 Add Optuna
 
V4.1:
 Add TPU

V4.2:
    1. reward function
        **change**

        ```
        # Before change
        def _reward_calculator(self, ball_x):
            # score & reward
            if self.steps < 2000:
                step_reward = self.steps * 0.01
            elif self.steps < 5000:
                step_reward = self.steps * 0.03
            else:
                step_reward = self.steps * 0.05

            rw = abs(ball_x - self.window_x/2)
            if rw < self.reward_width:
                x_axis_reward_rate = 1 + ((self.reward_width - abs(ball_x - self.window_x/2)) * self.x_axis_max_reward_rate)
                step_reward = self.steps * 0.01 * x_axis_reward_rate  # Simplified reward calculation
                return step_reward
            else:
                return 0
        ```

        ```
        # After change
        def _reward_calculator(self, ball_x):
            # score & reward
            step_reward = 1/100

            rw = abs(ball_x - self.window_x/2)
            if rw < self.reward_width:
                x_axis_reward_rate = 1 + ((self.reward_width - abs(ball_x - self.window_x/2)) * self.x_axis_max_reward_rate)
                step_reward = self.steps * 0.01 * x_axis_reward_rate  # Simplified reward calculation

                if self.steps % 500 == 0:
                    step_reward += self.steps/100

                return step_reward
            else:
                return 0
        ```

    2. Fixed the size of in-game objects changed to size base on the game window size