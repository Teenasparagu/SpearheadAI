import os
import random
import importlib
import math
from game_logic.units import Unit
from game_logic.board import Objective
from game_logic.terrain import RECTANGLE_WALL, L_SHAPE_WALL, rotate_shape, generate_spiral_offsets
from game_logic.factions.skaven import SkavenFactory
from game_logic.factions.stormcast import StormcastFactory

FACTIONS_PATH = "game_logic/factions"

def list_factions():
    return sorted([
        f.replace(".py", "") for f in os.listdir(FACTIONS_PATH)
        if f.endswith(".py") and not f.startswith("__") and f != "faction_factory.py"
    ])

def load_faction_force(faction_name, team_number):
    module = importlib.import_module(f"game_logic.factions.{faction_name}")
    factory_class = getattr(module, f"{faction_name.capitalize()}Factory")
    factory = factory_class()
    return factory.create_force(team=team_number)

def choose_faction():
    factions = list_factions()
    print("Choose your faction:")
    for i, name in enumerate(factions, start=1):
        print(f"{i}. {name.title()}")
    while True:
        try:
            choice = int(input("Enter number: "))
            if 1 <= choice <= len(factions):
                selected = factions[choice - 1]
                print(f"You chose: {selected.title()}")
                return selected
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

def roll_off():
    player_roll = int(input("Roll a D6: "))
    ai_roll = random.randint(1, 6)
    print(f"AI rolled: {ai_roll}")
    if player_roll > ai_roll:
        print("You win the roll-off!")
        role = input("Choose attacker or defender (a/d): ").strip().lower()
        return ("player", "ai") if role == "a" else ("ai", "player")
    elif ai_roll > player_roll:
        print("AI wins the roll-off.")
        role = random.choice(["attacker", "defender"])
        print(f"AI chooses to be {role}.")
        return ("ai", "player") if role == "attacker" else ("player", "ai")
    else:
        print("Tie! AI becomes attacker.")
        return "ai", "player"

def choose_battlefield():
    print("Choose battlefield: Aqshy or Ghyran")
    choice = input("(a/g): ").strip().lower()
    return "ghyran" if choice == "g" else "aqshy"

def get_objectives_for_battlefield(battlefield):
    if battlefield == "ghyran":
        return [
            Objective(1, 22),
            Objective(30, 22),
            Objective(58, 22),
            Objective(15, 7),
            Objective(45, 37),
        ]
    else:
        return [
            Objective(7, 7),
            Objective(51, 7),
            Objective(30, 22),
            Objective(10, 38),
            Objective(53, 38),
        ]



def choose_deployment_map():
    print("Choose deployment map:")
    print("1. Straight line (top vs bottom)")
    print("2. Diagonal (custom line)")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return "straight"
        elif choice == "2":
            return "diagonal"
        else:
            print("Invalid choice.")

def get_deployment_zones(board, map_type):
    if map_type == "straight":
        def defender_zone(x, y):
            return y < (board.height // 2) - 12

        def attacker_zone(x, y):
            return y >= (board.height // 2) + 12

    elif map_type == "diagonal":
        slope = (15 - 43) / (59 - 20)
        intercept = 43 - slope * 20

        def line_y(x): return slope * x + intercept

        def attacker_zone(x, y):
            return y > line_y(x)

        def defender_zone(x, y):
            flipped_x = 59 - x
            flipped_y = 43 - y
            return attacker_zone(flipped_x, flipped_y)
    else:
        raise ValueError(f"Unknown map type: {map_type}")

    return defender_zone, attacker_zone

def zone_description(zone_func, board, zone_name):
    if zone_name == "diagonal":
        return "Your deployment zone is a custom-shaped triangle defined by a diagonal from (20, 43) to (59, 15).\n" \
               "You may only place units on your side of the line. (No buffer visually applied yet.)"
    else:
        return f"Your deployment zone is a rectangle across half the board with a 6\" buffer from the center."

def deploy_units(board, units, territory_bounds, zone_name, player_label="Player"):
    print(zone_description(territory_bounds, board, zone_name))

    if zone_name == "straight":
        # Calculate bounds for rectangular deployment
        mid_y = board.height // 2
        buffer_cells = 12  # 6" buffer = 12 half-inch cells

        if player_label.lower() == "player":
            y_min = 0
            y_max = mid_y - buffer_cells - 1
        else:
            y_min = mid_y + buffer_cells
            y_max = board.height - 1

        x_min = 0
        x_max = board.width - 1

        print(f"{player_label}'s deployment zone:")
        print(f" - Top-left:     ({x_min}, {y_min})")
        print(f" - Top-right:    ({x_max}, {y_min})")
        print(f" - Bottom-left:  ({x_min}, {y_max})")
        print(f" - Bottom-right: ({x_max}, {y_max})")

    print(f"{player_label}, begin deploying your units:")

    for unit in units:
        if player_label.lower() == "ai":
            placed = False
            attempts = 100
            while not placed and attempts > 0:
                x = random.randint(0, board.width - 1)
                y = random.randint(0, board.height - 1)
                if territory_bounds(x, y):
                    unit.x = x
                    unit.y = y
                    for model in unit.models:
                        dx = x - unit.models[0].x
                        dy = y - unit.models[0].y
                        model.x += dx
                        model.y += dy
                    if all(0 <= mx < board.width and 0 <= my < board.height and board.grid[my][mx] == "-"
                           for model in unit.models for mx, my in model.get_occupied_squares()):
                        board.place_unit(unit)
                        placed = True
                attempts -= 1
            if not placed:
                print(f"⚠ AI could not place {unit.name} after 100 attempts.")
        else:
            while True:
                try:
                    print(f"\nPlacing {unit.name} (leader model):")
                    x, y = map(int, input("Enter x y within your deployment zone: ").split())
                    if territory_bounds(x, y):
                        unit.x = x
                        unit.y = y
                        board.place_unit(unit)
                        break
                    else:
                        print("❌ Not within your deployment zone.")
                except ValueError:
                    print("Invalid input. Use format: x y (e.g., 12 8)")

def describe_shape(name, shape):
    print(f"\n{name} shape (relative to origin 0,0):")
    for dx, dy in shape:
        print(f" - ({dx}, {dy})")

def get_deployment_bounds(zone):
    min_x = min(x for x, y in zone)
    max_x = max(x for x, y in zone)
    min_y = min(y for x, y in zone)
    max_y = max(y for x, y in zone)
    return min_x, min_y, max_x, max_y

def is_within_zone(x, y, rotated_shape, zone):
    zone_set = set(zone)
    for dx, dy in rotated_shape:
        if (x + dx, y + dy) not in zone_set:
            return False, (x + dx, y + dy)
    return True, None

def is_clear_of_objectives(x, y, rotated_shape, objectives):
    for dx, dy in rotated_shape:
        px, py = x + dx, y + dy
        for obj in objectives:
            if math.hypot(px - obj.x, py - obj.y) < 12:  # 6 inches = 12 tiles
                return False, (px, py)
    return True, None

def deploy_terrain(board, team, zone):
    from game_logic.terrain import RECTANGLE_WALL, L_SHAPE_WALL, rotate_shape, generate_spiral_offsets

    zone_name = "Player 1" if team == 1 else "Player 2"
    print(f"\n--- {zone_name} Terrain Deployment ---")

    min_x = min(x for x, y in zone)
    max_x = max(x for x, y in zone)
    min_y = min(y for x, y in zone)
    max_y = max(y for x, y in zone)
    print(f"{zone_name}'s deployment zone bounds: ({min_x},{min_y}) to ({max_x},{max_y})")

    for name, base_shape in [("Rectangle Wall", RECTANGLE_WALL), ("L-Shaped Wall", L_SHAPE_WALL)]:
        print(f"\n{name} shape (relative to origin 0,0):")
        for dx, dy in base_shape:
            print(f" - ({dx}, {dy})")

        if team == 2:
            print(f"AI is placing {name}...")
            attempts = 100
            directions = list(rotate_shape.__globals__["DIRECTION_VECTORS"].keys())
            for _ in range(attempts):
                x, y = random.choice(zone)
                direction = random.choice(directions)
                rotated = rotate_shape(base_shape, direction)

                legal_zone, _ = is_within_zone(x, y, rotated, zone)
                clear_obj, _ = is_clear_of_objectives(x, y, rotated, board.objectives)

                if legal_zone and clear_obj:
                    if board.place_terrain_piece(x, y, rotated):
                        print(f"✅ AI placed {name} at ({x}, {y}) facing {direction}")
                        break
            else:
                print(f"❌ AI failed to place {name} after 100 attempts.")
        else:
            while True:
                user_input = input(f"\nPlace {name} - Enter 'x y direction' or 'skip': ").strip().lower()
                if user_input == "skip":
                    print(f"Skipped placing {name}.")
                    break

                try:
                    parts = user_input.upper().split()
                    if len(parts) != 3:
                        raise ValueError("Invalid format. Use: x y direction")

                    x, y = int(parts[0]), int(parts[1])
                    direction = parts[2]
                    rotated = rotate_shape(base_shape, direction)

                    valid_zone, bad_tile = is_within_zone(x, y, rotated, zone)
                    valid_obj, obj_tile = is_clear_of_objectives(x, y, rotated, board.objectives)

                    if valid_zone and valid_obj:
                        if board.place_terrain_piece(x, y, rotated):
                            print(f"✅ Placed {name} at ({x},{y}) facing {direction}")
                            break
                        else:
                            print("❌ Unexpected error: placement failed despite passing checks.")
                    else:
                        if not valid_zone:
                            print(f"❌ Failed: Terrain extends outside deployment zone at {bad_tile}")
                        if not valid_obj:
                            print(f"❌ Failed: Too close to objective at {obj_tile}")

                        print("🔍 Searching for nearby valid placements...")
                        suggestions = []
                        for dx, dy in generate_spiral_offsets(4):
                            sx, sy = x + dx, y + dy
                            rotated = rotate_shape(base_shape, direction)
                            in_zone, _ = is_within_zone(sx, sy, rotated, zone)
                            clear_obj, _ = is_clear_of_objectives(sx, sy, rotated, board.objectives)
                            if in_zone and clear_obj:
                                suggestions.append((sx, sy))
                                if len(suggestions) == 3:
                                    break

                        if suggestions:
                            print("✅ Nearby valid options:")
                            for i, (sx, sy) in enumerate(suggestions):
                                print(f" {i+1}: ({sx}, {sy})")
                            choice = input("Select option 1-3 or press Enter to skip: ").strip()
                            if choice in ["1", "2", "3"]:
                                cx, cy = suggestions[int(choice)-1]
                                rotated = rotate_shape(base_shape, direction)
                                if board.place_terrain_piece(cx, cy, rotated):
                                    print(f"✅ Placed at fallback: ({cx}, {cy}) facing {direction}")
                                    break
                                else:
                                    print("❌ Failed to place at fallback location.")
                        else:
                            print("❌ No valid fallback placements within 2 inches.")
                except Exception as e:
                    print(f"⚠️ Error: {e}")

def deployment_phase(board):
    player_faction = choose_faction()
    ai_faction = random.choice([f for f in list_factions() if f != player_faction])
    print(f"AI is playing: {ai_faction.title()}")

    attacker, defender = roll_off()

    print("Choosing regiment abilities and enhancements... (placeholder)")

    battlefield = choose_battlefield()
    board.objectives = get_objectives_for_battlefield(battlefield)
    print("\nObjectives have been placed at:")
    for obj in board.objectives:
        print(f" - ({obj.x}, {obj.y})")


    deployment_map = choose_deployment_map()
    zone_name = deployment_map
    defender_zone, attacker_zone = get_deployment_zones(board, deployment_map)

    deploy_terrain(board, team=1 if defender == "player" else 2, zone=[
        (x, y) for x in range(board.width) for y in range(board.height) if defender_zone(x, y)
    ])
    deploy_terrain(board, team=1 if attacker == "player" else 2, zone=[
        (x, y) for x in range(board.width) for y in range(board.height) if attacker_zone(x, y)
    ])

    if defender == "player":
        player_units = load_faction_force(player_faction, team_number=1)
        ai_units = load_faction_force(ai_faction, team_number=2)
        deploy_units(board, player_units, defender_zone, zone_name, "Player")
        deploy_units(board, ai_units, attacker_zone, zone_name, "AI")
    else:
        ai_units = load_faction_force(ai_faction, team_number=1)
        player_units = load_faction_force(player_faction, team_number=2)
        deploy_units(board, ai_units, defender_zone, zone_name, "AI")
        deploy_units(board, player_units, attacker_zone, zone_name, "Player")

    if attacker == "player":
        choice = input("Do you want to go first or second? (first/second): ").strip().lower()
        first = "player" if choice == "first" else "ai"
    else:
        first = random.choice(["ai", "player"])
        print(f"AI chooses {first} to go first.")

    return player_units, ai_units, first
