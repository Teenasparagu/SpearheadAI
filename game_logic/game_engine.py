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

    def run_turn(self, team, get_input=input, log=print):
        """Run all phases for the given team."""
        self.game_state.current_turn_team = team

        log(f"\n-- {'Player' if team == 'player' else 'AI'} Turn --")
        log("\n[Start of Round Objective Check]")
        self.board.update_objective_control()
        self.board.display_objective_status()

        self.game_state.phase = "movement"
        if team == 'player':
            movement_phase.player_movement_phase(self.board, self.game_state.units['player'], get_input, log)
        else:
            movement_phase.ai_movement_phase(self.board, self.game_state.units['ai'], get_input, log)

        self.game_state.phase = "shooting"
        if team == 'player':
            shooting_phase.player_shooting_phase(self.board, self.game_state.units['player'], self.game_state.units['ai'], get_input, log)

        self.game_state.phase = "charge"
        if team == 'player':
            charge_phase.charge_phase(self.board, self.game_state.units['player'], get_input, log)
        else:
            charge_phase.ai_charge_phase(self.board, self.game_state.units['ai'], self.game_state.units['player'], get_input, log)

        self.game_state.phase = "combat"
        current_team_num = 1 if team == 'player' else 2
        combat_phase.combat_phase(self.board, current_team=current_team_num,
                                  player_units=self.game_state.units['player'],
                                  ai_units=self.game_state.units['ai'],
                                  get_input=get_input, log=log)

        self.game_state.phase = "end"
        end_units = self.game_state.units['player'] if team == 'player' else self.game_state.units['ai']
        victory_phase.process_end_phase_actions(self.board, end_units, get_input, log)

        log("\n[End of Round Objective Check]")
        self.board.update_objective_control()
        self.board.display_objective_status()

        self.game_state.phase = "victory"
        scoring_team = 1 if team == 'player' else 2
        victory_phase.calculate_victory_points(self.board, self.game_state.total_vp, scoring_team, get_input, log)

        # Prepare for next turn
        self.game_state.phase = "hero"

    def run_round(self, get_input=input, log=print):
        """Run a full round for both teams."""
        log(f"\n=== Round {self.game_state.round} Begins ===")

        if self.game_state.round > 1:
            log("\nRolling off for priority...")
            player_roll = random.randint(1, 6)
            ai_roll = random.randint(1, 6)
            log(f"You rolled a {player_roll}, AI rolled a {ai_roll}")

            if player_roll > ai_roll:
                choice = get_input("You win the roll-off. Go first or second? (first/second): ").strip().lower()
                self.game_state.current_priority = 'player' if choice == 'first' else 'ai'
            elif ai_roll > player_roll:
                self.game_state.current_priority = random.choice(['player', 'ai'])
                log(f"AI wins the roll-off and chooses to go {'first' if self.game_state.current_priority == 'ai' else 'second'}.")
            else:
                log("It's a tie! Player retains priority.")

        first = self.game_state.current_priority
        second = 'ai' if first == 'player' else 'player'

        self.run_turn(first, get_input, log)
        self.run_turn(second, get_input, log)

        self.game_state.round += 1

    def deployment_phase(self, get_input=input, log=print):
        """Run the deployment phase."""
        run_deployment_phase(self.game_state, self.board, get_input, log)

    def run_game(self, rounds=4, get_input=input, log=print):
        """Run a complete game via the CLI interface."""
        log("Welcome to Spearhead: Skirmish for the Realms!")
        log("==============================================")
        log("The battlefield awaits your command.\n")

        run_deployment_phase(self.game_state, self.board, get_input, log)

        for _ in range(1, rounds + 1):
            self.run_round(get_input, log)

        log("\n=== Game Over ===")
        log(
            f"Final Victory Points:\n  Player 1: {self.game_state.total_vp[1]}\n"
            f"Player 2: {self.game_state.total_vp[2]}"
        )
        if self.game_state.total_vp[1] > self.game_state.total_vp[2]:
            log(">> Player 1 wins!")
        elif self.game_state.total_vp[2] > self.game_state.total_vp[1]:
            log(">> Player 2 wins!")
        else:
            log(">> It's a tie!")


def run_deployment_phase(game_state, board, get_input, log):

    # Faction Selection
    player_faction = choose_faction(get_input, log)
    ai_faction = random.choice([f for f in list_factions() if f != player_faction])
    log(f"You chose: {player_faction.title()}")
    log(f"AI will play: {ai_faction.title()}")

    # Roll-Off
    attacker, defender = roll_off(get_input, log)
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
        enemy_zone=[(x, y) for x in range(board.width) for y in range(board.height) if attacker_zone(x, y)],
        get_input=get_input,
        log=log,
    )
    deploy_terrain(
        board,
        team=attacker_team,
        zone=[(x, y) for x in range(board.width) for y in range(board.height) if attacker_zone(x, y)],
        enemy_zone=[(x, y) for x in range(board.width) for y in range(board.height) if defender_zone(x, y)],
        get_input=get_input,
        log=log,
    )

    # Units
    if defender == "player":
        player_units = load_faction_force(player_faction, team_number=1)
        ai_units = load_faction_force(ai_faction, team_number=2)
        deploy_units(board, player_units, defender_zone, attacker_zone, zone_name, "Player", get_input, log)
        deploy_units(board, ai_units, attacker_zone, defender_zone, zone_name, "AI", get_input, log)
    else:
        ai_units = load_faction_force(ai_faction, team_number=1)
        player_units = load_faction_force(player_faction, team_number=2)
        deploy_units(board, ai_units, defender_zone, attacker_zone, zone_name, "AI", get_input, log)
        deploy_units(board, player_units, attacker_zone, defender_zone, zone_name, "Player", get_input, log)

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
