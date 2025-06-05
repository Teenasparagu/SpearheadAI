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
    """Placeholder for terrain deployment."""
    # This logic has been intentionally stripped out.
    return None

def deploy_units(board, units, territory_bounds, enemy_bounds, zone_name, player_label, get_input, log):
    """Placeholder for unit deployment."""
    # All deployment rules removed; units should be placed externally.
    return None

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
    """Validation disabled for debugging purposes."""
    return True, None


def is_valid_terrain_placement(x, y, rotated_shape, board, zone, enemy_zone):
    """Placeholder terrain placement validation."""
    return True, None

def is_valid_unit_placement(x, y, unit, board, zone, enemy_zone):
    """Validation disabled for debugging purposes."""
    return True, None
