import pymunk

try:
    from role.roles import Role
    from role.player import Player
    from role.platform import Platform
except ImportError:
    from game.role.roles import Role
    from game.role.player import Player
    from game.role.platform import Platform

class CollisionHandler:
    """Handles collision detection and response in the game."""

    def __init__(self, space: pymunk.Space):
        self.space = space
        self.players: dict[int, Player] = {}
        self.platforms: dict[int, Platform] = {}
        self.entities: dict[int, Role] = {}
        self.movable_objects: dict[int, Role] = {}

        # Set up collision handlers

    def setup_default_collision_handlers(self):
        self.movable_objects.update(self.players)
        self.movable_objects.update(self.entities)

        for movable_object_ct in self.movable_objects.keys():
            for platform_ct in self.platforms.keys():
                self.space.on_collision(movable_object_ct, platform_ct, post_solve=self.check_is_on_ground)

        for player_ct in self.players.keys():
            self.space.on_collision(player_ct, None, post_solve=self.check_is_collision_player_player)
            for entity_ct in self.entities.keys():
                self.space.on_collision(player_ct, entity_ct, post_solve=self.check_is_collision_player_entity)


    def check_is_on_ground(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        """Check if the player ball is on the ground (platform)"""
        obj = self.movable_objects.get(arbiter.shapes[0].collision_type)
        obj.set_is_on_ground(True)

    def check_is_collision_player_player(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        """Handle collisions between objects"""

        if arbiter.shapes[1].collision_type in self.players:  # Threshold for playing sound
            # self.players[arbiter.shapes[0].collision_type].set_is_alive(False)
            # self.players[arbiter.shapes[1].collision_type].set_is_alive(False)

            p1_v = self.players[arbiter.shapes[0].collision_type].get_velocity()
            p2_v = self.players[arbiter.shapes[1].collision_type].get_velocity()
            # TODO 速度更快的玩家將獲得獎勵
            pass

    def check_is_collision_player_entity(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        """Handle collisions between objects"""

        if arbiter.shapes[1].collision_type in self.players:  # Threshold for playing sound
            # self.players[arbiter.shapes[0].collision_type].set_is_alive(False)
            # self.players[arbiter.shapes[1].collision_type].set_is_alive(False)

            p1_v = self.players[arbiter.shapes[0].collision_type].get_velocity()
            p2_v = self.players[arbiter.shapes[1].collision_type].get_velocity()
            # TODO 速度更快的玩家將獲得獎勵
            pass

    def set_players(self, players: list[Player]):
        self.players = {player.get_collision_type(): player for player in players}

    def set_platforms(self, platforms: list[Platform]):
        self.platforms = {platform.get_collision_type(): platform for platform in platforms}
    
    def set_entities(self, entities: list[list[Role]]):
        for _entities in entities:
            self.entities = {entity.get_collision_type(): entity for entity in _entities}