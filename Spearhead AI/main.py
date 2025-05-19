import random
from game_logic.board import Board
from game_phases.movement_phase import player_movement_phase, ai_movement_phase
from game_phases.charge_phase import charge_phase, ai_charge_phase
from game_phases.deployment import deployment_phase

def main():
    print("Welcome to Spearhead: Skirmish for the Realms!")
    print("==============================================")
    print("The battlefield awaits your command.\n")

    # Initialize game board
    board = Board(width=60, height=44)

    # Run deployment phase (handles faction choice, terrain, objectives, and unit placement)
    player_units, ai_units, first = deployment_phase(board)

    # Start rounds
    for round_num in range(1, 6):
        print(f"\n=== Round {round_num} Begins ===")

        if first == "player":
            player_turn(board, player_units)
            ai_turn(board, player_units, ai_units)
        else:
            ai_turn(board, player_units, ai_units)
            player_turn(board, player_units)

        board.update_objective_control()

        # Alternate who goes first next round
        first = "ai" if first == "player" else "player"

    print("\nGame Over.")

def player_turn(board, player_units):
    print("\n-- Player Turn --")
    # future: hero_phase(board, player_units)
    player_movement_phase(board, player_units)
    # future: shooting_phase(board, player_units)
    charge_phase(board, player_units)
    # future: combat_phase(board, player_units)
    # future: end_phase(board, player_units)

def ai_turn(board, player_units, ai_units):
    print("\n-- AI Turn --")
    # future: ai_hero_phase(...)
    ai_movement_phase(board, ai_units)
    # future: ai_shooting_phase(...)
    ai_charge_phase(board, ai_units, player_units)
    # future: ai_combat_phase(...)
    # future: ai_end_phase(...)

if __name__ == "__main__":
    main()
