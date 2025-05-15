from func import Train

train = Train( 
    load_model="./best_model_V4.4", 
    obs_type="state_based", 
    n_envs=1
)

train.evaluate(
    n_episodes=3, 
    difficulty="medium"
)