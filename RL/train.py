import sys
import os

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.vec_env import VecNormalize

# Go up one level from the current notebook's directory to the project root
project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import from the project root
from game.gym_env import BalancingBallEnv
from RL.levels.level3.config import model_config, train_config

class Train:
    def __init__(self,
                 model_cfg: model_config=None,
                 train_cfg: train_config=None,
                 n_envs: int=None,
                 load_model=None,
                ):

        # Create directories
        os.makedirs(train_cfg.tensorboard_log, exist_ok=True)
        os.makedirs(train_cfg.model_dir, exist_ok=True)
        self.model_cfg = model_cfg
        self.train_cfg = train_cfg
        self.log_dir = train_cfg.tensorboard_log
        self.model_dir = train_cfg.model_dir
        self.n_envs = n_envs
        self.obs_type = model_cfg.model_obs_type

        # Setup environments
        env = make_vec_env(
            self.make_env(),
            n_envs=n_envs
        )
        self.env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)


        # Setup evaluation environment
        eval_env = make_vec_env(
            self.make_env(),
            n_envs=1
        )
        self.eval_env = eval_env

        # Create the PPO model
        if load_model:
            print(f"Loading model from {load_model}")
            self.model = PPO.load(
                load_model,
                env=self.env,
                tensorboard_log=self.log_dir,
            )
        else:

            print("obs type: ", self.obs_type)

            # PPO for continuous action space with adversarial training
            self.model = PPO(
                env=self.env,
                tensorboard_log=self.log_dir,
                **model_cfg.model_param
            )

        # Setup callbacks
        self.checkpoint_callback = CheckpointCallback(
            save_freq=train_cfg.save_freq // self.n_envs,  # Divide by n_envs as save_freq is in timesteps
            save_path=self.model_dir,
            name_prefix="ppo_balancing_ball_" + str(self.obs_type),
        )

        self.eval_callback = EvalCallback(
            self.eval_env,
            best_model_save_path=self.model_dir,
            log_path=self.log_dir,
            eval_freq=train_cfg.eval_freq // self.n_envs,
            n_eval_episodes=train_cfg.eval_episodes,
            deterministic=True,
            render=False
        )

    def make_env(self):
        """
        Create and return an environment function to be used with VecEnv
        """
        def _init():
            env = BalancingBallEnv(
                render_mode=self.train_cfg.render_mode,
                model_cfg=self.model_cfg,
                train_cfg=self.train_cfg,
            )
            return env
        return _init

    def train_ppo(self):
        """
        Train a PPO agent to play the Balancing Ball game
        """


        # Train the model
        print("Starting training...")
        self.model.learn(
            total_timesteps=self.train_cfg.total_timesteps,
            callback=[self.checkpoint_callback, self.eval_callback],
        )

        # Save the final model
        self.model.save(f"{self.model_dir}/ppo_balancing_ball_final_" + str(self.obs_type))

        print("Training completed!")
        return self.model

    def evaluate(self, n_episodes=10, deterministic: bool = None):
        """
        Evaluate a trained model

        Args:
            model_path: Path to the saved model
            n_episodes: Number of episodes to evaluate on
        """
        # Load the model

        # Evaluate
        mean_reward, std_reward = evaluate_policy(
            self.model,
            self.env,
            n_eval_episodes=n_episodes,
            deterministic=deterministic,
            render=True
        )

        print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")

        self.env.close()

    def test_env_with_random_action(self, n_episodes=5):
        """
        Test the environment by taking random actions

        Args:
            n_episodes: Number of episodes to run
        """
        for episode in range(n_episodes):
            obs, info = self.env.reset()
            done = False
            total_reward = 0
            step = 0

            print(f"Starting episode {episode+1}")

            while not done:
                action = [self.env.action_space.sample() for _ in range(self.n_envs)]
                obs, reward, done, info = self.env.step(action)

                total_reward += reward
                step += 1

            print(f"Episode {episode+1} finished after {step} steps with total reward {total_reward}")

        self.env.close()

# if args.mode == "train":
#     train_ppo(
#         total_timesteps=args.timesteps,
#         n_envs=args.n_envs,
#         load_model=args.load_model,
#         eval_episodes=args.eval_episodes,
#     )
# else:
#     if args.load_model is None:
#         print("Error: Must provide --load_model for evaluation")
#     else:
#         evaluate(
#             model_path=args.load_model,
#             n_episodes=args.eval_episodes,
#         )

if __name__ == "__main__":
    n_envs = 1

    # Choose whether to do hyperparameter optimization or direct training
    do_optimization = False

    model_cfg = model_config()
    train_cfg = train_config()
    train_cfg.render_mode = "human"  # Set render mode to human for visualization

    if do_optimization: # game_screen, state_based
        # from RL.optuna import Optuna_optimize
        
        # optuna_optimizer = Optuna_optimize(obs_type=model_cfg.model_obs_type, level=1)
        # n_trials = 10
        # best_trial = optuna_optimizer.optuna_parameter_tuning(n_trials=n_trials)
        # print(f"best_trial found: {best_trial}")

        pass
    else:
        # Create trainer for adversarial training
        from RL.train import Train
        training = Train(
            model_cfg=model_cfg,
            train_cfg=train_cfg,
            n_envs=n_envs,
            load_model=None,  # Start fresh for adversarial training
        )

        model = training.train_ppo()

        print("Adversarial training completed!")