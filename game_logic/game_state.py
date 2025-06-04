# game_logic/game_state.py
import numpy as np

class GameState:
    def __init__(self, board):
        self.board = board
        self.width = board.width
        self.height = board.height
        self.terrain = board.terrain
        self.objectives = board.objectives
        self.realm = None
        self.map_layout = None
        self.phase = "deployment"
        self.round = 1
        self.current_priority = "player"
        self.total_vp = {1: 0, 2: 0}

        # New clean unit tracking
        self.units = {"player": [], "ai": []}
        self.players = {"attacker": None, "defender": None}
        self.turn_order = []
        self.current_turn_team = None

        self.messages = []

        # Deployment helpers for web UI
        self.pending_units = []
        self.player_zone = set()
        self.enemy_zone = set()
        self.pending_first = None

    def to_grid_dict(self):
        grid = {}

        for y in range(self.height):
            for x in range(self.width):
                grid[(x, y)] = {
                    "terrain": 0,
                    "objective": 0,
                    "control1": 0,
                    "control2": 0,
                    "team1": 0,
                    "team2": 0,
                    "leader1": 0,
                    "leader2": 0,
                    "move_range": 0,
                    "control_score": 0
                }

        # Mark terrain
        for tx, ty in self.terrain:
            if (tx, ty) in grid:
                grid[(tx, ty)]["terrain"] = 1

        # Mark objectives and control
        for obj in self.objectives:
            if (obj.x, obj.y) in grid:
                grid[(obj.x, obj.y)]["objective"] = 1
                team = obj.control_team
                if team == 1:
                    grid[(obj.x, obj.y)]["control1"] = 1
                elif team == 2:
                    grid[(obj.x, obj.y)]["control2"] = 1

        # Mark units and stats
        for unit in self.units["player"] + self.units["ai"]:
            for i, model in enumerate(unit.models):
                if 0 <= model.x < self.width and 0 <= model.y < self.height:
                    tile = grid[(model.x, model.y)]
                    if unit.team == 1:
                        tile["team1"] = 1
                        if i == 0:
                            tile["leader1"] = 1
                    else:
                        tile["team2"] = 1
                        if i == 0:
                            tile["leader2"] = 1
                    tile["move_range"] = unit.move_range / 12  # Normalize max 12"
                    tile["control_score"] = unit.control_score / 5  # Assume max 5

        return grid

    def to_tensor(self):
        grid_dict = self.to_grid_dict()
        channel_keys = ["terrain", "objective", "control1", "control2", "team1", "team2", "leader1", "leader2", "move_range", "control_score"]
        tensor = np.zeros((len(channel_keys), self.height, self.width), dtype=np.float32)

        for (x, y), features in grid_dict.items():
            for i, key in enumerate(channel_keys):
                tensor[i, y, x] = features.get(key, 0)

        return tensor

    def log_message(self, msg: str):
        self.messages.append(msg)
