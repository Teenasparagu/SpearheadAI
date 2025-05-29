import random
from game_logic.board import Board
from game_phases.movement_phase import player_movement_phase, ai_movement_phase
from game_phases.charge_phase import charge_phase, ai_charge_phase
from game_phases.deployment import deployment_phase
from game_phases.victory_phase import process_end_phase_actions, calculate_victory_points
from game_phases.shooting_phase import player_shooting_phase
from game_phases.combat_phase import combat_phase

def main():
    print("Welcome to Spearhead: Skirmish for the Realms!")
    print("==============================================")
    print("The battlefield awaits your command.\n")

    # Track total VPs
    total_vp = {1: 0, 2: 0}

    # Initialize game board
    board = Board(width=60, height=44)

    # Deployment phase handles setup and initial priority
    player_units, ai_units, current_priority = deployment_phase(board)

    # Game Rounds
    for round_num in range(1, 5):
        print(f"\n=== Round {round_num} Begins ===")

        # Roll-off for priority from round 2 onward
        if round_num > 1:
            print("\nRolling off for priority...")
            player_roll = random.randint(1, 6)
            ai_roll = random.randint(1, 6)
            print(f"You rolled a {player_roll}, AI rolled a {ai_roll}")

            if player_roll > ai_roll:
                choice = input("You win the roll-off. Go first or second? (first/second): ").strip().lower()
                current_priority = "player" if choice == "first" else "ai"
            elif ai_roll > player_roll:
                current_priority = random.choice(["player", "ai"])
                print(f"AI wins the roll-off and chooses to go {'first' if current_priority == 'ai' else 'second'}.")
            else:
                print("It's a tie! Player retains priority.")

        # Execute turns based on priority
        if current_priority == "player":
            player_turn(board, player_units, ai_units, total_vp)
            ai_turn(board, player_units, ai_units, total_vp)
        else:
            ai_turn(board, player_units, ai_units, total_vp)
            player_turn(board, player_units, ai_units, total_vp)

    # Final results
    print("\n=== Game Over ===")
    print(f"Final Victory Points:\n  Player 1: {total_vp[1]}\n  Player 2: {total_vp[2]}")
    if total_vp[1] > total_vp[2]:
        print(">> Player 1 wins!")
    elif total_vp[2] > total_vp[1]:
        print(">> Player 2 wins!")
    else:
        print(">> It's a tie!")

def player_turn(board, player_units, ai_units, total_vp):
    print("\n-- Player Turn --")

    print("\n[Start of Round Objective Check]")
    board.update_objective_control()
    board.display_objective_status()

    # Movement
    player_movement_phase(board, player_units)

    # Shooting
    player_shooting_phase(board, player_units, ai_units)


    # Charge
    charge_phase(board, player_units)

    # Combat
    combat_phase(board, current_team=1, player_units=player_units, ai_units=ai_units)

    # End Phase Actions
    process_end_phase_actions(board, player_units)

    print("\n[End of Round Objective Check]")
    board.update_objective_control()
    board.display_objective_status()

    # Scoring
    calculate_victory_points(board, total_vp, scoring_team=1)

def ai_turn(board, player_units, ai_units, total_vp):
    print("\n-- AI Turn --")
    print("\n[Start of Round Objective Check]")
    board.update_objective_control()
    board.display_objective_status()
    ai_movement_phase(board, ai_units)
    ai_charge_phase(board, ai_units, player_units)
    combat_phase(board, current_team=1, player_units=player_units, ai_units=ai_units)
    process_end_phase_actions(board, ai_units)
    print("\n[End of Round Objective Check]")
    board.update_objective_control()
    board.display_objective_status()
    calculate_victory_points(board, total_vp, scoring_team=2)

if __name__ == "__main__":
    main()
