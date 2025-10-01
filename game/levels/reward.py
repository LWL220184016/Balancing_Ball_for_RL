
設計一個 reward 類，裏面有很多不同函數來做多個不同方面的 reward 計算比如：
玩家掉出平臺
玩家撞擊實體
玩家生存時間
玩家速度獎勵

class RewardCalculator:
    """判斷和計算遊戲中各種情況下的獎勵和懲罰"""

    def __init__(self, reward_parameters: dict):
        
        # define reward parameters
        for key, value in reward_parameters.items():
            setattr(self, key, value)

    def check_is_fall_off_platform(self, fallen: bool) -> float:
        """計算玩家掉出平臺的懲罰"""
        if fallen:
            penalty = -10.0
            self.total_reward += penalty
            return penalty
        return 0.0

    def reward_collision(self, collided: bool) -> float:
        """計算玩家撞擊實體的懲罰"""
        if collided:
            penalty = -5.0
            self.total_reward += penalty
            return penalty
        return 0.0

    def reward_survival_time(self, time_survived: float) -> float:
        """根據玩家生存時間給予獎勵"""
        reward = time_survived * 0.1  # 每秒生存獲得0.1獎勵
        self.total_reward += reward
        return reward

    def reward_speed(self, speed: float) -> float:
        """根據玩家速度給予獎勵"""
        if speed > 5.0:  # 假設速度大於5.0有額外獎勵
            reward = (speed - 5.0) * 0.2
            self.total_reward += reward
            return reward
        return 0.0

    def get_total_reward(self) -> float:
        """返回總獎勵值"""
        return self.total_reward