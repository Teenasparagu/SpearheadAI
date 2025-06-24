import math
import random
from game_logic.units import is_in_combat


def player_movement_phase(board, player_units, get_input, log):
    log("\n--- Movement Phase ---")

    controlled = [obj for obj in board.objectives if obj.control_team]
    if controlled:
        for obj in controlled:
            log(f"Team {obj.control_team} controls objective at ({obj.x}, {obj.y})")
    else:
        log("No objectives currently controlled.")

    for unit in player_units:
        player_unit_move(unit, board, get_input, log)

direction_map = {
    "n": (0, -1), "nne": (1, -2), "ne": (1, -1), "ene": (2, -1),
    "e": (1, 0), "ese": (2, 1), "se": (1, 1), "sse": (1, 2),
    "s": (0, 1), "ssw": (-1, 2), "sw": (-1, 1), "wsw": (-2, 1),
    "w": (-1, 0), "wnw": (-2, -1), "nw": (-1, -1), "nnw": (-1, -2),
    "north": (0, -1), "northeast": (1, -1), "east": (1, 0),
    "southeast": (1, 1), "south": (0, 1), "southwest": (-1, 1),
    "west": (-1, 0), "northwest": (-1, -1)
}


def attempt_move(unit, board, move_input, move_range, log):
    """Handle a single move command like 'ne 5'. Returns True if moved."""
    try:
        direction_str, inches_str = move_input.split()
        inches = float(inches_str)
    except ValueError:
        log("Invalid input. Format: 'ne 5'.")
        return False

    if direction_str not in direction_map:
        log("Invalid direction. Try 'n', 'sw', 'sse', etc.")
        return False

    distance_squares = inches * 2
    dx, dy = direction_map[direction_str]
    vector_length = math.sqrt(dx ** 2 + dy ** 2)
    if vector_length == 0:
        log("Invalid direction vector.")
        return False

    dx_norm = dx / vector_length
    dy_norm = dy / vector_length
    dest_x = unit.x + int(round(dx_norm * distance_squares))
    dest_y = unit.y + int(round(dy_norm * distance_squares))

    if not (0 <= dest_x < board.width and 0 <= dest_y < board.height):
        log("Move out of bounds!")
        return False

    actual_dist = math.sqrt((dest_x - unit.x) ** 2 + (dest_y - unit.y) ** 2)
    if actual_dist > move_range:
        log(
            f"{unit.name} can't move that far (max {move_range / 2:.1f} inches)."
        )
        return False

    if is_in_combat(dest_x, dest_y, board, unit.team):
        log("Destination too close to an enemy unit.")
        return False

    return board.move_unit(unit, dest_x, dest_y)

def move_input_loop(unit, board, move_range, get_input, log):
    moved = False
    while True:
        log("Enter direction and distance (e.g., 'ne 5') or type 'skip':")
        move_input = get_input(">> ").strip().lower()

        if move_input == "skip":
            log(f"{unit.name} skipped their move.")
            break

        try:
            direction_str, inches_str = move_input.split()
            inches = float(inches_str)

            if direction_str not in direction_map:
                log("Invalid direction. Try 'n', 'sw', 'sse', etc.")
                continue

            # Convert inches to grid units
            distance_squares = inches * 2
            dx, dy = direction_map[direction_str]

            # Normalize the direction vector
            vector_length = math.sqrt(dx**2 + dy**2)
            if vector_length == 0:
                log("Invalid direction vector.")
                continue

            dx_normalized = dx / vector_length
            dy_normalized = dy / vector_length

            # Calculate proposed destination
            dest_x = unit.x + int(round(dx_normalized * distance_squares))
            dest_y = unit.y + int(round(dy_normalized * distance_squares))

            # Check bounds
            if not (0 <= dest_x < board.width and 0 <= dest_y < board.height):
                log("Move out of bounds!")
                continue

            # Check if within move range (Euclidean check)
            actual_dist = math.sqrt((dest_x - unit.x)**2 + (dest_y - unit.y)**2)
            if actual_dist > move_range:
                log(f"{unit.name} can't move that far (max {move_range / 2:.1f} inches).")
                continue

            # Check enemy proximity
            if is_in_combat(unit.models[0].x, unit.models[0].y, board, unit.team):
                log("You cannot end your move within 3 inches of an enemy unit (must charge to do so).")
                continue

            success = board.move_unit(unit, dest_x, dest_y)
            if success:
                moved = True
                break
            else:
                log("Invalid move. Try again.")
        except ValueError:
            log("Invalid input. Format: 'ne 5' or 'skip'.")

    if moved:
        adjust_unit_formation(unit, board, get_input, log)




def normal_move(unit, board, get_input, log):
    move_range = unit.move_range  # in squares
    unit.has_run = False
    log(f"Normal move range: {move_range / 2:.1f} inches")

    move_input_loop(unit, board, move_range, get_input, log)

def run_move(unit, board, get_input, log):
    run_bonus = random.randint(1, 6)
    move_range = unit.move_range + run_bonus * 2  # in squares
    unit.has_run = True
    log(f"Running! Rolled a {run_bonus}. Total range: {move_range / 2:.1f} inches")

    move_input_loop(unit, board, move_range, get_input, log)


def player_unit_move(unit, board, get_input, log):
    """Interactive movement for a single unit."""
    log(f"\n{unit.name} starts at ({unit.x}, {unit.y})")

    if is_in_combat(unit.models[0].x, unit.models[0].y, board, unit.team):
        log(f"{unit.name} is in combat.")
        choice = get_input("Retreat? (y/n): ").strip().lower()
        if choice in ["y", "yes"]:
            while True:
                move_input = get_input(
                    "Enter retreat direction and distance or 'skip': "
                ).strip().lower()
                if move_input == "skip":
                    log(f"{unit.name} skipped their retreat.")
                    break
                if attempt_move(unit, board, move_input, unit.move_range, log):
                    dmg = random.randint(1, 3)
                    log(f"{unit.name} suffers {dmg} damage while retreating!")
                    unit.apply_damage(dmg)
                    break
        else:
            log(f"{unit.name} ends its movement without retreating.")
        return

    choice = get_input("Choose movement - N = No Move, M = Move, R = Run: ")
    choice = choice.strip().lower()
    if choice.startswith("n"):
        log(f"{unit.name} does not move.")
        return

    if choice.startswith("r"):
        run_bonus = random.randint(1, 6)
        move_range = unit.move_range + run_bonus * 2
        unit.has_run = True
        log(f"Running! Rolled a {run_bonus}. Total range: {move_range / 2:.1f} inches")
    else:
        move_range = unit.move_range
        unit.has_run = False
        log(f"Normal move range: {move_range / 2:.1f} inches")

    while True:
        move_input = get_input("Enter direction and distance or 'skip': ").strip().lower()
        if move_input == "skip":
            log(f"{unit.name} skipped their move.")
            break
        if attempt_move(unit, board, move_input, move_range, log):
            break

def retreat_move(unit, board, get_input, log):
    log(f"{unit.name} is retreating.")
    move_range = unit.move_range
    unit.has_run = True  # Retreat disables charge/shoot

    while True:
        log(f"You may retreat up to {move_range / 2:.1f} inches.")
        log("Enter direction and distance (e.g., 'southwest 5') or type 'skip':")
        move_input = get_input(">> ").strip().lower()

        if move_input == "skip":
            log(f"{unit.name} skipped their retreat.")
            return

        try:
            direction_str, inches_str = move_input.split()
            inches = float(inches_str)
            distance_squares = inches * 2

            if direction_str not in direction_map:
                log("Invalid direction. Try 'n', 'sw', 'sse', etc.")
                continue

            if distance_squares > move_range:
                log(f"You cannot retreat more than {move_range / 2:.1f} inches.")
                continue

            dx, dy = direction_map[direction_str]
            vector_length = math.sqrt(dx**2 + dy**2)
            if vector_length == 0:
                log("Invalid direction.")
                continue

            dx_normalized = dx / vector_length
            dy_normalized = dy / vector_length

            dest_x = unit.x + int(round(dx_normalized * distance_squares))
            dest_y = unit.y + int(round(dy_normalized * distance_squares))


            if is_in_combat(unit.models[0].x, unit.models[0].y, board, unit.team):
                log("Retreat destination is too close to an enemy. Try a different direction.")
                continue

            success = board.move_unit(unit, dest_x, dest_y)
            if success:
                # ✅ Apply D3 mortal wounds after retreating
                dmg = random.randint(1, 3)
                log(f"{unit.name} suffers {dmg} damage while retreating!")
                unit.apply_damage(dmg)
                adjust_unit_formation(unit, board, get_input, log)
            return
        except ValueError:
            log("Invalid input. Use format like 'sw 4.5' or 'skip'.")


                
def ai_movement_phase(board, ai_units, get_input, log):
    """AI skips movement for now."""
    log("\nAI's Turn:")
    for unit in ai_units:
        unit.has_run = False
        log(f"{unit.name} does not move.")


# Additional helpers for web interface movement


def move_unit_to(unit, board, dest_x, dest_y, move_range, log):
    """Move a unit to an explicit destination, enforcing distance and proximity checks."""
    if not (0 <= dest_x < board.width and 0 <= dest_y < board.height):
        log("Move out of bounds!")
        return False

    dx = dest_x - unit.x
    dy = dest_y - unit.y
    distance = math.sqrt(dx**2 + dy**2)
    if distance > move_range:
        log(f"{unit.name} can't move that far (max {move_range / 2:.1f} inches).")
        return False

    if is_in_combat(dest_x, dest_y, board, unit.team):
        log("Destination too close to an enemy unit.")
        return False

    path = board.get_path(unit.x, unit.y, dest_x, dest_y)
    blocked, blocked_tile = board.is_path_blocked(path, (unit.x, unit.y), unit)
    if blocked:
        log(f"Path is blocked at {blocked_tile}.")
        return False

    # Delegate to board.move_unit which now handles formation movement
    success = board.move_unit(unit, dest_x, dest_y)
    if success:
        log(f"{unit.name} moved to ({dest_x}, {dest_y}).")
    return success


def adjust_unit_formation(unit, board, get_input, log):
    """Allow the player to manually reposition models after a move."""
    log("Adjust unit formation? (y/n):")
    choice = get_input(">> ").strip().lower()
    if choice not in ["y", "yes"]:
        return

    for idx in range(1, len(unit.models)):
        model = unit.models[idx]
        while True:
            log(f"Place model {idx} at 'x y' or type 'skip':")
            resp = get_input(">> ").strip().lower()
            if resp == "skip":
                break
            try:
                x_str, y_str = resp.split()
                x = int(x_str)
                y = int(y_str)
            except ValueError:
                log("Invalid format. Use 'x y' or 'skip'.")
                continue

            if board.move_model(unit, idx, x, y):
                break
            else:
                log("Invalid position. Try again.")
