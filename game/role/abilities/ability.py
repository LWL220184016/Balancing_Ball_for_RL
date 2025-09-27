
class Ability:
    def __init__(self, name: str, cooldown: float):
        self.name = name
        self.cooldown = cooldown  # Cooldown time in seconds
        self.last_used_time = 0  # Timestamp of the last use
    pass