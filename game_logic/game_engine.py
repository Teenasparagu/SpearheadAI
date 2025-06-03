# game_logic/game_engine.py
from game_logic.board import Board
from game_logic.game_state import GameState
from game_phases import movement_phase, shooting_phase, combat_phase, charge_phase, deployment,victory_phase, hero_phase, end_phase, round_start

class GameEngine:
    def __init__(self):
        self.board = Board(60, 44)
        self.game_state = GameState(self.board)
        self.round = 1
        self.current_priority = "player"
        self.setup_complete = False

    def deploy(self, faction, realm, map_type):
        # Use deployment_phase module to perform setup
        ...
        self.setup_complete = True

    def step(self, action_dict):
        """
        Takes a single action:
        - movement
        - shooting
        - charging
        - etc.
        """
        phase = action_dict["phase"]
        if phase == "movement":
            movement_phase.player_movement_phase(self.board, self.game_state.player_units, action_dict)
        elif phase == "shooting":
            shooting_phase.player_shooting_phase(self.board, ...)
        # Add more phases as needed

        return self.game_state.to_grid_dict()

    def advance_round(self):
        self.round += 1
        self.board.update_objective_control()
        # Possibly roll for new priority
