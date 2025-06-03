import random
from game_logic.board import Board
from game_logic.game_state import GameState
from game_phases.deployment import deployment_phase
from game_phases.movement_phase import player_movement_phase, ai_movement_phase
from game_phases.charge_phase import charge_phase, ai_charge_phase
from game_phases.victory_phase import process_end_phase_actions, calculate_victory_points
from game_phases.shooting_phase import player_shooting_phase
from game_phases.combat_phase import combat_phase

def main():
    print("Welcome to Spearhead: Skirmish for the Realms!")
    print("==============================================")
    print("The battlefield awaits your command.\n")

    board = Board(width=60, height=44)
    game_state = GameState(board)

    # Deployment returns units and starting priority
    player_units, ai_units, priority = deployment_phase(game_state.board)

    game_state.player_units = player_units
    game_state.ai_units = ai_units
    game_state.current_priority = priority

    for round_num in range(1, 5):
        print(f"\n=== Round {round_num} Begins ===")
        game_state.round = round_num

        if round_num > 1:
            print("\nRolling off for priority...")
            player_roll = random.randint(1, 6)
            ai_roll = random.randint(1, 6)
            print(f"You rolled a {player_roll}, AI rolled a {ai_roll}")

            if player_roll > ai_roll:
                choice = input("You win the roll-off. Go first or second? (first/second): ").strip().lower()
                game_state.current_priority = "player" if choice == "first" else "ai"
            elif ai_roll > player_roll:
                game_state.current_priority = random.choice(["player", "ai"])
                print(f"AI wins the roll-off and chooses to go {'first' if game_state.current_priority == 'ai' else 'second'}.")
            else:
                print("It's a tie! Player retains priority.")

        if game_state.current_priority == "player":
            player_turn(game_state)
            ai_turn(game_state)
        else:
            ai_turn(game_state)
            player_turn(game_state)

    print("\n=== Game Over ===")
    print(f"Final Victory Points:\n  Player 1: {game_state.total_vp[1]}\n  Player 2: {game_state.total_vp[2]}")
    if game_state.total_vp[1] > game_state.total_vp[2]:
        print(">> Player 1 wins!")
    elif game_state.total_vp[2] > game_state.total_vp[1]:
        print(">> Player 2 wins!")
    else:
        print(">> It's a tie!")

def player_turn(game_state):
    board = game_state.board
    print("\n-- Player Turn --")

    print("\n[Start of Round Objective Check]")
    board.update_objective_control()
    board.display_objective_status()

    player_movement_phase(board, game_state.player_units)
    player_shooting_phase(board, game_state.player_units, game_state.ai_units)
    charge_phase(board, game_state.player_units)
    combat_phase(board, current_team=1, player_units=game_state.player_units, ai_units=game_state.ai_units)
    process_end_phase_actions(board, game_state.player_units)

    print("\n[End of Round Objective Check]")
    board.update_objective_control()
    board.display_objective_status()
    calculate_victory_points(board, game_state.total_vp, scoring_team=1)

def ai_turn(game_state):
    board = game_state.board
    print("\n-- AI Turn --")

    print("\n[Start of Round Objective Check]")
    board.update_objective_control()
    board.display_objective_status()

    ai_movement_phase(board, game_state.ai_units)
    ai_charge_phase(board, game_state.ai_units, game_state.player_units)
    combat_phase(board, current_team=2, player_units=game_state.player_units, ai_units=game_state.ai_units)
    process_end_phase_actions(board, game_state.ai_units)

    print("\n[End of Round Objective Check]")
    board.update_objective_control()
    board.display_objective_status()
    calculate_victory_points(board, game_state.total_vp, scoring_team=2)

if __name__ == "__main__":
    main()
