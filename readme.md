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

V4.3:
    1. Add frame skipping to make the frame data input to the model change more obvious (removed)
    The model performs an action once and then continues the action for a certain number of frames, while collecting and stacking frames to predict the next action for the model. 
    For example, if a cycle is 6 frames, then the model will perform an action for 6 frames, and stack the 6 frames to predict the next action for the model.

    2. add _reward_calculator2
    def _reward_calculator2(self, ball_x):
        # Base reward for staying alive
        step_reward = 0.1
        
        # Distance from center (normalized)
        distance_from_center = abs(ball_x - self.window_x/2) / (self.window_x/2)
        
        # Smooth reward based on position (highest at center)
        position_reward = max(0, 1.0 - distance_from_center)
        
        # Apply position reward (with higher weight for better position)
        step_reward += position_reward * 0.3
        
        # Small bonus for surviving longer (but not dominant)
        survival_bonus = min(0.2, self.steps / 10000)
        step_reward += survival_bonus
    
        # Checkpoint bonuses remain meaningful but don't explode
        if self.steps % 1000 == 0 and self.steps > 0:
            step_reward += 1.0
            print(f"Checkpoint reached: {self.steps}")
            
        return step_reward

V4.4:
    Add state base observation and training output

V4.5:
    Add grayscale and resize the game screen image, improve code format

V5:
    Add Level system

V6: 
    Add Level3 for Two-player confrontation

V6: 
    training env for Two-player confrontation