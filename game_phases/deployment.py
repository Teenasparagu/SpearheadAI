import os
import random
import importlib
import math
from game_logic.units import Unit, Model
from game_logic.board import Objective
from game_logic.terrain import RECTANGLE_WALL, L_SHAPE_WALL, rotate_shape, generate_spiral_offsets
from game_logic.board import TILE_OBJECTIVE
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

def choose_faction(get_input, log):
    factions = list_factions()
    log("Choose your faction:")
    for i, name in enumerate(factions, start=1):
        log(f"{i}. {name.title()}")
    while True:
        try:
            choice = int(get_input("Enter number:"))
            if 1 <= choice <= len(factions):
                selected = factions[choice - 1]
                log(f"You chose: {selected.title()}")
                return selected
            else:
                log("Invalid selection.")
        except ValueError:
            log("Please enter a number.")

def roll_off(get_input, log):
    player_roll = random.randint(1, 6)
    ai_roll = random.randint(1, 6)
    log(f"Player rolled: {player_roll}")
    log(f"AI rolled: {ai_roll}")
    if player_roll > ai_roll:
        log("You win the roll-off!")
        role = get_input("Choose attacker or defender (a/d):").strip().lower()
        return ("player", "ai") if role == "a" else ("ai", "player")
    elif ai_roll > player_roll:
        log("AI wins the roll-off.")
        role = random.choice(["attacker", "defender"])
        log(f"AI chooses to be {role}.")
        return ("ai", "player") if role == "attacker" else ("player", "ai")
    else:
        log("Tie! AI becomes attacker.")
        return "ai", "player"

def choose_battlefield(get_input, log):
    log("Choose battlefield: Aqshy or Ghyran")
    choice = get_input("(a/g):").strip().lower()
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

def choose_deployment_map(get_input, log):
    log("Choose deployment map:")
    log("1. Straight line (top vs bottom)")
    log("2. Diagonal (custom line)")
    while True:
        choice = get_input("Enter 1 or 2:").strip()
        if choice == "1":
            return "straight"
        elif choice == "2":
            return "diagonal"
        else:
            log("Invalid choice.")


def _triangle_offsets(num, orientation):
    """Offsets for a triangle formation behind the leader."""
    offsets = [(0, 0)]
    placed = 1
    row = 2
    y = -orientation
    while placed < num:
        start_x = -(row - 1)
        for i in range(row):
            if placed >= num:
                break
            offsets.append((start_x + 2 * i, y))
            placed += 1
        row += 1
        y -= orientation
    return offsets


def _rectangle_offsets(num, orientation):
    """Offsets for a simple rectangular block behind the leader."""
    offsets = [(0, 0)]
    cols = math.ceil(math.sqrt(num))
    rows = math.ceil(num / cols)
    placed = 1
    for r in range(rows):
        if placed >= num:
            break
        y = -(r + 1) * orientation
        start_x = -(cols - 1)
        for c in range(cols):
            if placed >= num:
                break
            offsets.append((start_x + 2 * c, y))
            placed += 1
    return offsets


def _circle_offsets(num, orientation):
    """Offsets spreading models in a semicircle behind the leader."""
    offsets = [(0, 0)]
    spiral = generate_spiral_offsets(radius=6)
    for dx, dy in spiral[1:]:
        if len(offsets) >= num:
            break
        if -orientation * dy >= 0:
            offsets.append((dx, dy))
    for dx, dy in spiral[1:]:
        if len(offsets) >= num:
            break
        if -orientation * dy < 0:
            offsets.append((dx, dy))
    return offsets[:num]


def formation_offsets(formation, num_models, orientation):
    formation = (formation or "triangle").lower()
    if formation.startswith("box") or formation.startswith("rect"):
        return _rectangle_offsets(num_models, orientation)
    if formation.startswith("circle"):
        return _circle_offsets(num_models, orientation)
    return _triangle_offsets(num_models, orientation)

def get_deployment_zones(board, map_type):
    if map_type == "straight":
        mid = board.height // 2

        def defender_zone(x, y):
            return y < mid

        def attacker_zone(x, y):
            return y >= mid

    elif map_type == "diagonal":
        slope = (15 - 43) / (59 - 20)
        intercept = (board.height / 2) - slope * (board.width / 2)

        def line_y(x): return slope * x + intercept

        def attacker_zone(x, y):
            return y >= line_y(x)

        def defender_zone(x, y):
            return y < line_y(x)
    else:
        raise ValueError(f"Unknown map type: {map_type}")

    return defender_zone, attacker_zone

def deploy_terrain(board, team, zone, enemy_zone, get_input, log):
    zone_name = "Player 1" if team == 1 else "Player 2"
    log(f"{zone_name} Terrain Deployment")

    for name, base_shape in [("Rectangle Wall", RECTANGLE_WALL), ("L-Shaped Wall", L_SHAPE_WALL)]:
        if team == 2:
            log(f"AI is placing {name}...")
            attempts = 100
            directions = list(rotate_shape.__globals__["DIRECTION_VECTORS"].keys())
            for _ in range(attempts):
                x, y = random.choice(zone)
                direction = random.choice(directions)
                rotated = rotate_shape(base_shape, direction)
                legal, _ = is_valid_terrain_placement(x, y, rotated, board, zone, enemy_zone)

                if legal:
                    if board.place_terrain_piece(x, y, rotated):
                        log(f"✅ AI placed {name} at ({x}, {y}) facing {direction}")
                        break
            else:
                log(f"❌ AI failed to place {name} after 100 attempts.")
        else:
            while True:
                user_input = get_input(f"Place {name} - Enter 'x y direction' or 'skip':").strip().lower()
                if user_input == "skip":
                    log(f"Skipped placing {name}.")
                    break
                try:
                    parts = user_input.upper().split()
                    if len(parts) != 3:
                        raise ValueError("Invalid format. Use: x y direction")
                    x, y = int(parts[0]), int(parts[1])
                    direction = parts[2]
                    rotated = rotate_shape(base_shape, direction)
                    valid, _ = is_valid_terrain_placement(x, y, rotated, board, zone, enemy_zone)
                    if valid:
                        if board.place_terrain_piece(x, y, rotated):
                            log(f"✅ Placed {name} at ({x},{y}) facing {direction}")
                            break
                        else:
                            log("❌ Unexpected error: placement failed despite passing checks.")
                    else:
                        log("❌ Placement invalid.")
                except Exception as e:
                    log(f"⚠️ Error: {e}")

def deploy_units(board, units, territory_bounds, enemy_bounds, zone_name, player_label, get_input, log):
    zone_coords = [(i, j) for i in range(board.width) for j in range(board.height) if territory_bounds(i, j)]
    enemy_coords = [(i, j) for i in range(board.width) for j in range(board.height) if enemy_bounds(i, j)]
    zone_list = zone_coords
    center_y = sum(y for _, y in zone_list) / len(zone_list)
    orientation = 1 if center_y < board.height / 2 else -1

    for unit in units:
        if player_label.lower() == "ai":
            placed = False
            attempts = 100
            while not placed and attempts > 0:
                x = random.randint(0, board.width - 1)
                y = random.randint(0, board.height - 1)
                if territory_bounds(x, y):
                    offsets = formation_offsets("box", len(unit.models), orientation)
                    for i, (dx, dy) in enumerate(offsets):
                        unit.models[i].x = x + dx
                        unit.models[i].y = y + dy
                    unit.x, unit.y = x, y
                    valid, _ = is_valid_unit_placement(x, y, unit, board, zone_coords, enemy_coords)
                    if valid and board.place_unit(unit):
                        placed = True
                attempts -= 1
            if not placed:
                log(f"⚠ AI could not place {unit.name} after 100 attempts.")
        else:
            while True:
                try:
                    pos = get_input(f"Placing {unit.name} leader x y:").split()
                    x, y = map(int, pos)
                    if not territory_bounds(x, y):
                        log("❌ Not within your deployment zone.")
                        continue
                    ok, reason = is_valid_leader_position(x, y, board, zone_coords, enemy_coords)
                    if not ok:
                        log(f"❌ Placement invalid: {reason}")
                        continue
                    formation = get_input("Choose formation (box/triangle/circle):").strip().lower()
                    offsets = formation_offsets(formation, len(unit.models), orientation)
                    for i, (dx, dy) in enumerate(offsets):
                        unit.models[i].x = x + dx
                        unit.models[i].y = y + dy
                    unit.x, unit.y = x, y
                    valid, reason = is_valid_unit_placement(x, y, unit, board, zone_coords, enemy_coords)
                    if not valid:
                        log(f"❌ Placement invalid: {reason}")
                        continue
                    log("Proposed positions:")
                    for i, m in enumerate(unit.models):
                        log(f"  Model {i} -> ({m.x}, {m.y})")
                    confirm = get_input("Confirm placement? (y/n):").strip().lower()
                    if confirm.startswith("y"):
                        board.place_unit(unit)
                        log(f"Placed {unit.name}")
                        break
                    manual = get_input("Manual placement instead? (y/n):").strip().lower()
                    if not manual.startswith("y"):
                        continue
                    positions = []
                    for idx in range(len(unit.models)):
                        mx, my = map(int, get_input(f"Model {idx} x y:").split())
                        positions.append((mx, my))
                    for idx, (mx, my) in enumerate(positions):
                        unit.models[idx].x = mx
                        unit.models[idx].y = my
                    unit.x, unit.y = positions[0]
                    valid, reason = is_valid_unit_placement(unit.x, unit.y, unit, board, zone_coords, enemy_coords)
                    if valid and board.place_unit(unit):
                        log(f"Placed {unit.name}")
                        break
                    else:
                        log(f"❌ Manual placement invalid: {reason}")
                except ValueError:
                    log("Invalid input. Use format: x y (e.g., 12 8)")

def is_within_zone(x, y, rotated_shape, zone):
    zone_set = set(zone)
    for dx, dy in rotated_shape:
        if (x + dx, y + dy) not in zone_set:
            return False, (x + dx, y + dy)
    return True, None

def is_clear_of_objectives(x, y, rotated_shape, board):
    for dx, dy in rotated_shape:
        px, py = x + dx, y + dy
        if board.grid[py][px] == TILE_OBJECTIVE:
            return False, (px, py)
    return True, None


def is_valid_leader_position(x, y, board, zone, enemy_zone):
    """Check leader tile only before generating a formation."""
    if (x, y) not in set(zone):
        return False, "Outside deployment zone"
    # Allow placement closer to the board edge than units, but still keep a
    # minimal buffer so models don't start hanging off the map. Six squares
    # gives players room to position leaders while leaving space for formations.
    if x < 6 or y < 6 or x >= board.width - 6 or y >= board.height - 6:
        return False, "Too close to board edge"
    if board.grid[y][x] != "-":
        return False, "Tile occupied"
    for ex, ey in enemy_zone:
        if math.hypot(x - ex, y - ey) < 12:
            return False, "Too close to enemy zone"
    for tx, ty in board.terrain:
        if math.hypot(x - tx, y - ty) < 12:
            return False, "Too close to terrain"
    return True, None


def is_valid_terrain_placement(x, y, rotated_shape, board, zone, enemy_zone):
    zone_set = set(zone)
    enemy_set = set(enemy_zone)
    for dx, dy in rotated_shape:
        px, py = x + dx, y + dy
        if (px, py) not in zone_set:
            return False, (px, py)
        if not (6 <= px < board.width - 6 and 6 <= py < board.height - 6):
            return False, (px, py)
        for ex, ey in enemy_set:
            if math.hypot(px - ex, py - ey) < 6:
                return False, (px, py)
        if board.grid[py][px] == TILE_OBJECTIVE:
            return False, (px, py)
        for tx, ty in board.terrain:
            if math.hypot(px - tx, py - ty) < 12:
                return False, (px, py)
    return True, None

def is_valid_unit_placement(x, y, unit, board, zone, enemy_zone):
    """Validate a unit placement. Returns (bool, reason)."""
    zone_set = set(zone)
    enemy_set = set(enemy_zone)

    dx = x - unit.models[0].x
    dy = y - unit.models[0].y

    new_positions = []
    for model in unit.models:
        mx = model.x + dx
        my = model.y + dy
        temp = Model(mx, my, base_diameter=model.base_diameter)
        new_positions.append((mx, my, temp.get_occupied_squares()))

    for _, _, squares in new_positions:
        for px, py in squares:
            if not (0 <= px < board.width and 0 <= py < board.height):
                return False, "Out of bounds"
            # Models need a little breathing room from the table edge but can be
            # closer than the earlier 12 square requirement.
            if px < 6 or py < 6 or px >= board.width - 6 or py >= board.height - 6:
                return False, "Too close to board edge"
            if board.grid[py][px] != "-":
                return False, "Tile occupied"
            if (px, py) not in zone_set:
                return False, "Outside deployment zone"
            for ex, ey in enemy_set:
                if math.hypot(px - ex, py - ey) < 12:
                    return False, "Too close to enemy zone"

    for i, (mx, my, _) in enumerate(new_positions):
        coherent = False
        for j, (ox, oy, _) in enumerate(new_positions):
            if i != j and math.sqrt((mx - ox) ** 2 + (my - oy) ** 2) <= 2:
                coherent = True
                break
        if not coherent:
            return False, "Models not coherent"

    return True, None
