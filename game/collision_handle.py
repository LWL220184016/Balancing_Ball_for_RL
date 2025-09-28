import pymunk

try:
    from role.player import Player
    from role.platform import Platform
except ImportError:
    from game.role.player import Player
    from game.role.platform import Platform

class CollisionHandler:
    """Handles collision detection and response in the game."""

    def __init__(self, space: pymunk.Space, players: list[Player], platforms: list[Platform]):
        self.space = space
        self.players = {player.get_collision_type(): player for player in players}
        self.platforms = {platform.get_collision_type(): platform for platform in platforms}
        self.loop = 0


    def check_is_on_ground(self):
        """Check if the player is on the ground (platform)"""
        self.loop += 1
        # Set up collision handlers
        for player_ct in self.players.keys():
            self.players[player_ct].set_is_on_ground(False)  # Reset before checking
            for platform_ct in self.platforms.keys():
                self.space.on_collision(player_ct, platform_ct, post_solve=self._check_is_on_ground)

    def _check_is_on_ground(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        """Check if the player ball is on the ground (platform)"""
        self.players[arbiter.shapes[0].collision_type].set_is_on_ground(True)
        
    
    def check_is_collision_player(self):
        """Check for collisions between players and handle them"""

        for player_ct in self.players.keys():
            self.space.on_collision(player_ct, None, post_solve=self._check_is_collision_player)

    def _check_is_collision_player(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        """Handle collisions between objects"""

        if arbiter.shapes[1].collision_type in self.players:  # Threshold for playing sound
            # self.players[arbiter.shapes[0].collision_type].set_is_alive(False)
            # self.players[arbiter.shapes[1].collision_type].set_is_alive(False)

            p1_v = self.players[arbiter.shapes[0].collision_type].get_velocity()
            p2_v = self.players[arbiter.shapes[1].collision_type].get_velocity()
            # TODO 速度更快的玩家將獲得獎勵
            pass