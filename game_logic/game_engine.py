# game_logic/game_engine.py
import random
import math
from game_logic.board import Board
from game_logic.game_state import GameState
from game_phases import movement_phase, shooting_phase, combat_phase, charge_phase, deployment,victory_phase, hero_phase, end_phase, round_start
from game_phases.deployment import (
    choose_faction, list_factions, roll_off, choose_battlefield,
    get_objectives_for_battlefield, choose_deployment_map,
    get_deployment_zones, deploy_terrain, deploy_units, load_faction_force
)

class GameEngine:
    def __init__(self):
        self.board = Board(60, 44)
        self.game_state = GameState(self.board)
        self.round = 1
        self.current_priority = "player"
        self.setup_complete = False


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


def run_deployment_phase(game_state, board, get_input, log):

    # Faction Selection
    player_faction = choose_faction(get_input, log)
    ai_faction = random.choice([f for f in list_factions() if f != player_faction])
    log(f"You chose: {player_faction.title()}")
    log(f"AI will play: {ai_faction.title()}")

    # Roll-Off
    attacker, defender = roll_off()
    log(f"{attacker.capitalize()} is the attacker, {defender} is the defender.")

    # Placeholder enhancement step
    log("Choosing regiment abilities and enhancements... (placeholder)")

    # Realm & Objective Placement
    battlefield = choose_battlefield(get_input, log)
    game_state.realm = battlefield
    board.objectives = get_objectives_for_battlefield(battlefield)
    game_state.objectives = board.objectives
    log(f"Objectives placed for {battlefield.title()}:")
    for obj in board.objectives:
        log(f" - ({obj.x}, {obj.y})")

    # Deployment Map
    deployment_map = choose_deployment_map(get_input, log)
    game_state.map_layout = deployment_map
    zone_name = deployment_map
    defender_zone, attacker_zone = get_deployment_zones(board, deployment_map)

    # Terrain
    defender_team = 1 if defender == "player" else 2
    attacker_team = 1 if attacker == "player" else 2

    deploy_terrain(
        board,
        team=defender_team,
        zone=[(x, y) for x in range(board.width) for y in range(board.height) if defender_zone(x, y)],
        get_input=get_input,
        log=log,
    )
    deploy_terrain(
        board,
        team=attacker_team,
        zone=[(x, y) for x in range(board.width) for y in range(board.height) if attacker_zone(x, y)],
        get_input=get_input,
        log=log,
    )

    # Units
    if defender == "player":
        player_units = load_faction_force(player_faction, team_number=1)
        ai_units = load_faction_force(ai_faction, team_number=2)
        deploy_units(board, player_units, defender_zone, zone_name, "Player", get_input, log)
        deploy_units(board, ai_units, attacker_zone, zone_name, "AI", get_input, log)
    else:
        ai_units = load_faction_force(ai_faction, team_number=1)
        player_units = load_faction_force(player_faction, team_number=2)
        deploy_units(board, ai_units, defender_zone, zone_name, "AI", get_input, log)
        deploy_units(board, player_units, attacker_zone, zone_name, "Player", get_input, log)

    game_state.players["attacker"] = attacker
    game_state.players["defender"] = defender
    game_state.units["player"] = player_units
    game_state.units["ai"] = ai_units

    # Determine First Turn
    if attacker == "player":
        choice = get_input("Do you want to go first or second? (first/second): ").strip().lower()
        first = "player" if choice == "first" else "ai"
    else:
        first = random.choice(["ai", "player"])
        log(f"AI chooses {first} to go first.")

    game_state.phase = "hero"
    game_state.turn_order = [first, "ai" if first == "player" else "player"]
    log(f"{first.capitalize()} will take the first turn.")
    log("Deployment phase complete.")
