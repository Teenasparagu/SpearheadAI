import math
import random

def is_in_combat(unit, board, combat_range=6):
    """Check if this unit is within 3\" (6 squares) of any enemy model."""
    for model in unit.models:
        for enemy_unit in board.units:
            if enemy_unit.team == unit.team:
                continue  # Skip friendly units

            for enemy_model in enemy_unit.models:
                dx = model.x - enemy_model.x
                dy = model.y - enemy_model.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist <= combat_range:
                    return True
    return False


def is_too_close_to_enemy(x, y, board, team, radius=6):
    for enemy_unit in board.units:
        if enemy_unit.team != team:
            for model in enemy_unit.models:
                if math.sqrt((x - model.x)**2 + (y - model.y)**2) < radius:
                    return True
    return False


def player_movement_phase(board, player_units):
    print("\n--- Movement Phase ---")

    controlled = [obj for obj in board.objectives if obj.control_team]
    if controlled:
        for obj in controlled:
            print(f"Team {obj.control_team} controls objective at ({obj.x}, {obj.y})")
    else:
        print("No objectives currently controlled.")

    for unit in player_units:
        print(f"\n{unit.name} starts at ({unit.x}, {unit.y})")

        if is_in_combat(unit, board):
            print(f"{unit.name} is in combat.")
            choice = input("Retreat? (Y/N): ").strip().lower()
            if choice in ["y", "yes"]:
                retreat_move(unit, board)
                continue
            else:
                print(f"{unit.name} ends its movement without retreating.")
                continue


        print("Choose movement type: (N = Normal Move, R = Run +D6 inches)")
        move_type = input(">> ").strip().lower()

        if move_type == "r":
            run_move(unit, board)
        else:
            normal_move(unit, board)

direction_map = {
    "n": (0, -1), "nne": (1, -2), "ne": (1, -1), "ene": (2, -1),
    "e": (1, 0), "ese": (2, 1), "se": (1, 1), "sse": (1, 2),
    "s": (0, 1), "ssw": (-1, 2), "sw": (-1, 1), "wsw": (-2, 1),
    "w": (-1, 0), "wnw": (-2, -1), "nw": (-1, -1), "nnw": (-1, -2),
    "north": (0, -1), "northeast": (1, -1), "east": (1, 0),
    "southeast": (1, 1), "south": (0, 1), "southwest": (-1, 1),
    "west": (-1, 0), "northwest": (-1, -1)
}

def move_input_loop(unit, board, move_range):
    while True:
        print("Enter direction and distance (e.g., 'ne 5') or type 'skip':")
        move_input = input(">> ").strip().lower()

        if move_input == "skip":
            print(f"{unit.name} skipped their move.")
            break

        try:
            direction_str, inches_str = move_input.split()
            inches = float(inches_str)

            if direction_str not in direction_map:
                print("Invalid direction. Try 'n', 'sw', 'sse', etc.")
                continue

            # Convert inches to grid units
            distance_squares = inches * 2
            dx, dy = direction_map[direction_str]

            # Normalize the direction vector
            vector_length = math.sqrt(dx**2 + dy**2)
            if vector_length == 0:
                print("Invalid direction vector.")
                continue

            dx_normalized = dx / vector_length
            dy_normalized = dy / vector_length

            # Calculate proposed destination
            dest_x = unit.x + int(round(dx_normalized * distance_squares))
            dest_y = unit.y + int(round(dy_normalized * distance_squares))

            # Check bounds
            if not (0 <= dest_x < board.width and 0 <= dest_y < board.height):
                print("Move out of bounds!")
                continue

            # Check if within move range (Euclidean check)
            actual_dist = math.sqrt((dest_x - unit.x)**2 + (dest_y - unit.y)**2)
            if actual_dist > move_range:
                print(f"{unit.name} can't move that far (max {move_range / 2:.1f} inches).")
                continue

            # Check enemy proximity
            if is_too_close_to_enemy(dest_x, dest_y, board, unit.team):
                print("You cannot end your move within 3 inches of an enemy unit (must charge to do so).")
                continue

            success = board.move_unit(unit, dest_x, dest_y)
            if success:
                break
            else:
                print("Invalid move. Try again.")
        except ValueError:
            print("Invalid input. Format: 'ne 5' or 'skip'.")




def normal_move(unit, board):
    move_range = unit.move_range  # in squares
    unit.has_run = False
    print(f"Normal move range: {move_range / 2:.1f} inches")

    move_input_loop(unit, board, move_range)

def run_move(unit, board):
    run_bonus = random.randint(1, 6)
    move_range = unit.move_range + run_bonus * 2  # in squares
    unit.has_run = True
    print(f"Running! Rolled a {run_bonus}. Total range: {move_range / 2:.1f} inches")

    move_input_loop(unit, board, move_range)

def retreat_move(unit, board):
    print(f"{unit.name} is retreating.")
    move_range = unit.move_range
    unit.has_run = True  # Retreat disables charge/shoot

    while True:
        print(f"You may retreat up to {move_range / 2:.1f} inches.")
        print("Enter direction and distance (e.g., 'southwest 5') or type 'skip':")
        move_input = input(">> ").strip().lower()

        if move_input == "skip":
            print(f"{unit.name} skipped their retreat.")
            return

        try:
            direction_str, inches_str = move_input.split()
            inches = float(inches_str)
            distance_squares = inches * 2

            if direction_str not in direction_map:
                print("Invalid direction. Try 'n', 'sw', 'sse', etc.")
                continue

            if distance_squares > move_range:
                print(f"You cannot retreat more than {move_range / 2:.1f} inches.")
                continue

            dx, dy = direction_map[direction_str]
            vector_length = math.sqrt(dx**2 + dy**2)
            if vector_length == 0:
                print("Invalid direction.")
                continue

            dx_normalized = dx / vector_length
            dy_normalized = dy / vector_length

            dest_x = unit.x + int(round(dx_normalized * distance_squares))
            dest_y = unit.y + int(round(dy_normalized * distance_squares))


            if is_too_close_to_enemy(dest_x, dest_y, board, unit.team):
                print("Retreat destination is too close to an enemy. Try a different direction.")
                continue

            success = board.move_unit(unit, dest_x, dest_y)
            if success:
                # ✅ Apply D3 mortal wounds after retreating
                dmg = random.randint(1, 3)
                print(f"{unit.name} suffers {dmg} damage while retreating!")
                unit.apply_damage(dmg)
            return
        except ValueError:
            print("Invalid input. Use format like 'sw 4.5' or 'skip'.")


                
def ai_movement_phase(board, ai_units):
    print("\nAI's Turn:")
    for unit in ai_units:
        if is_in_combat(unit, board):
            print(f"{unit.name} is in combat and cannot move unless retreating.")
            continue

        # Decide whether to run (50% chance)
        will_run = random.choice([True, False])
        move_range = unit.move_range
        unit.has_run = False

        if will_run:
            run_bonus = random.randint(1, 6)
            move_range += run_bonus * 2
            unit.has_run = True
            print(f"{unit.name} chooses to Run! (Rolled {run_bonus})")

        # Try up to 10 directions
        for _ in range(10):
            direction = random.choice(list(direction_map.keys()))
            inches = round(random.uniform(1, move_range / 2), 1)
            dx, dy = direction_map[direction]
            dest_x = unit.x + int(round(dx * inches * 2))
            dest_y = unit.y + int(round(dy * inches * 2))

            if not (0 <= dest_x < board.width and 0 <= dest_y < board.height):
                continue
            if is_too_close_to_enemy(dest_x, dest_y, board, unit.team):
                continue

            print(f"{unit.name} attempting to move {inches} inches toward {direction} to ({dest_x}, {dest_y})...")
            success = board.move_unit(unit, dest_x, dest_y)
            if success:
                break  # ✅ move only once per turn
        else:
            print(f"{unit.name} couldn't find a valid direction to move.")


        