
class Platform:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def get_info(self):
        return f"Platform: {self.name}, Description: {self.description}"