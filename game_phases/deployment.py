import os
import random
import importlib
from game_logic.units import Unit
from game_logic.board import Objective

FACTIONS_PATH = "game_logic/factions"

def list_factions():
    return sorted([
        f.replace(".py", "") for f in os.listdir(FACTIONS_PATH)
        if f.endswith(".py") and not f.startswith("__")
    ])

def load_faction_force(faction_name, team_number):
    module = importlib.import_module(f"game_logic.factions." + faction_name)
    return module.create_force(team=team_number)

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
            Objective(10, 7),
            Objective(7, 37),
            Objective(30, 22),
            Objective(53, 6),
            Objective(50, 37),
        ]
    else:
        return [
            Objective(12, 5),
            Objective(45, 8),
            Objective(30, 22),
            Objective(12, 35),
            Objective(45, 38),
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

def zone_description(zone_func, board, zone_name):
    if zone_name == "diagonal":
        return "Your deployment zone is a custom-shaped triangle defined by a diagonal from (20, 43) to (59, 15).\n" \
               "You may only place units on your side of the line. (No buffer visually applied yet.)"
    else:
        return f"Your deployment zone is a rectangle across half the board with a 6\" buffer from the center."

def deploy_units(board, units, territory_bounds, zone_name, player_label="Player"):
    print(zone_description(territory_bounds, board, zone_name))
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

def deploy_terrain(board, phase):
    print(f"{phase.capitalize()} is placing terrain. For now, this is placeholder logic.")
    pass

def deployment_phase(board):
    player_faction = choose_faction()
    ai_faction = random.choice([f for f in list_factions() if f != player_faction])
    print(f"AI is playing: {ai_faction.title()}")

    attacker, defender = roll_off()

    print("Choosing regiment abilities and enhancements... (placeholder)")

    battlefield = choose_battlefield()
    board.objectives = get_objectives_for_battlefield(battlefield)

    deployment_map = choose_deployment_map()
    buffer = 0  # No buffer for now

    if deployment_map == "straight":
        def defender_zone(x, y): return y < (board.height // 2) - 12
        def attacker_zone(x, y): return y >= (board.height // 2) + 12
        zone_name = "straight"
    else:
        # Diagonal from (20, 43) to (59, 15)
        slope = (15 - 43) / (59 - 20)
        intercept = 43 - slope * 20

        def line_y(x): return slope * x + intercept

        def attacker_zone(x, y): return y > line_y(x)

        def defender_zone(x, y):
            flipped_x = 59 - x
            flipped_y = 43 - y
            return attacker_zone(flipped_x, flipped_y)

        zone_name = "diagonal"

    deploy_terrain(board, defender)
    deploy_terrain(board, attacker)

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
