
    def _setup_pygame(self):
        """Set up PyGame for rendering"""
        pygame.init()
        self.frame_count = 0

        if self.sound_enabled:
            self._load_sounds()

        if self.render_mode == "human":
            self.screen = pygame.display.set_mode((self.window_x, self.window_y))
            pygame.display.set_caption("Balancing Ball - Indie Game")
            self.font = pygame.font.Font(None, int(self.window_x / 34))

        elif self.render_mode == "rgb_array":
            self.screen = pygame.Surface((self.window_x, self.window_y))

        elif self.render_mode == "rgb_array_and_human": # todo
            print("rgb_array_and_human mode is not supported yet.")

        elif self.render_mode == "rgb_array_and_human_in_colab": # todo
            from pymunk.pygame_util import DrawOptions

            self.screen = pygame.Surface((self.window_x, self.window_y))  # Create hidden surface

            # Set up display in Colab
            self.draw_options = DrawOptions(self.screen)
            html_display = ipd.HTML('''
                <div id="pygame-output" style="width:100%;">
                    <img id="pygame-img" style="width:100%;">
                </div>
            ''')
            self.display_handle = display(html_display, display_id='pygame_display')

            self.last_update_time = time.time()
            self.update_interval = 1.0 / 15  # Update display at 15 FPS to avoid overwhelming Colab
            self.font = pygame.font.Font(None, int(self.window_x / 34))


        else:
            print("Invalid render mode. Using headless mode.")

        self.clock = pygame.time.Clock()

        # Create custom draw options for indie style

    def _load_sounds(self):
        """Load game sound effects"""
        try:
            pygame.mixer.init()
            self.sound_bounce = pygame.mixer.Sound("assets/bounce.wav") if os.path.exists("assets/bounce.wav") else None
            self.sound_fall = pygame.mixer.Sound("assets/fall.wav") if os.path.exists("assets/fall.wav") else None
        except Exception:
            print("Sound loading error")
            self.sound_enabled = False
            pass

    def _apply_difficulty(self):
        """Apply difficulty settings to the game"""
        if self.difficulty == "easy":
            self.max_platform_speed = 1.5
            self.ball_elasticity = 0.5
        elif self.difficulty == "medium":
            self.max_platform_speed = 2.5
            self.ball_elasticity = 0.7
        else:  # hard
            self.max_platform_speed = 3.5
            self.ball_elasticity = 0.9

        # self.circle.shape.elasticity = self.ball_elasticity

    def reset(self) -> np.ndarray:
        """Reset the game state and return the initial observation"""
        # Reset physics objects
        self.level.reset()

        # Reset game state
        self.steps = 0
        self.start_time = time.time()
        self.game_over = False
        self.score = [0] * self.num_players
        self.winner = None
        self.player_alive = [True] * self.num_players
        self.last_speeds = [0] * self.num_players

        # Return initial observation
        return self._get_observation()

    def step(self, actions: list = []) -> Tuple[np.ndarray, list, bool, Dict]:
        """
        Take a step in the game using the given actions.

        Args:
            actions: List of continuous actions [-1.0, 1.0] for each player controlling horizontal force

        Returns:
            observation: Game state observation
            rewards: List of rewards for each player
            terminated: Whether episode is done
            info: Additional information
        """
        # Apply actions to players (horizontal forces)
        for i in range(len(self.dynamic_body_players)):
            if i < len(actions) and self.player_alive[i]:
                # Scale action to force range
                force_magnitude = actions[i] * self.max_force
                force_vector = pymunk.Vec2d(force_magnitude, 0)
                self.dynamic_body_players[i].apply_force_at_world_point(
                    force_vector, 
                    self.dynamic_body_players[i].position
                )

        self.level.action()

        # Step the physics simulation
        self.space.step(1/self.fps)

        # Check game state
        self.steps += 1
        terminated = False
        rewards = [0] * self.num_players

        # Check collision reward if available
        collision_occurred = getattr(self.level, 'collision_occurred', False)
        
        # Check if balls fall off screen and calculate rewards
        alive_count = 0
        for i, player in enumerate(self.dynamic_body_players):
            if not self.player_alive[i]:
                continue
                
            ball_x = player.position[0]
            ball_y = player.position[1]
            
            # Check if player falls
            if (ball_y > self.kinematic_body_platforms[0].position[1] + 50 or
                ball_x < 0 or ball_x > self.window_x):
                
                self.player_alive[i] = False
                rewards[i] = self.penalty_falling
                
                # Give collision reward to remaining players if collision occurred recently
                if collision_occurred:
                    for j in range(self.num_players):
                        if j != i and self.player_alive[j]:
                            rewards[j] += self.collision_reward
                
                if self.sound_enabled and self.sound_fall:
                    self.sound_fall.play()
            else:
                alive_count += 1
                # Calculate survival and performance rewards
                survival_reward = self.reward_staying_alive
                
                # Speed reward - encourage maintaining movement
                current_speed = abs(player.velocity[0]) + abs(player.velocity[1])
                speed_reward = current_speed * self.speed_reward_multiplier
                self.last_speeds[i] = current_speed
                
                # Centered position reward
                center_reward = self._calculate_center_reward(ball_x)
                
                rewards[i] = survival_reward + speed_reward + center_reward
                self.score[i] += rewards[i]

        # Check if game should end
        if alive_count <= 1 or self.steps >= self.max_step:
            terminated = True
            self.game_over = True
            
            # Determine winner (last player alive or highest score)
            if alive_count == 1:
                self.winner = next(i for i in range(self.num_players) if self.player_alive[i])
                # Give bonus to winner
                rewards[self.winner] += 10.0
            elif alive_count == 0:
                self.winner = None  # Draw
            else:
                # Game ended due to max steps, winner is highest score
                self.winner = np.argmax(self.score)

            result = {
                "game_total_duration": f"{time.time() - self.start_time:.2f}",
                "scores": self.score,
                "winner": self.winner,
                "steps": self.steps
            }
            self.recorder.add_no_limit(result)

        return self._get_observation(), rewards, terminated

    def _calculate_center_reward(self, ball_x):
        """Calculate reward based on how close ball is to center"""
        distance_from_center = abs(ball_x - self.window_x/2)
        if distance_from_center < self.reward_width:
            normalized_distance = distance_from_center / self.reward_width
            return self.reward_ball_centered * (1.0 - normalized_distance)
        return 0
