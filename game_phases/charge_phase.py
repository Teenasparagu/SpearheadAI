import math
import random

def is_near_enemy(unit, board, within_inches=12):
    limit = within_inches * 2
    for model in unit.models:
        for enemy_unit in board.units:
            if enemy_unit.team != unit.team:
                for enemy_model in enemy_unit.models:
                    dist = math.sqrt((model.x - enemy_model.x)**2 + (model.y - enemy_model.y)**2)
                    if dist <= limit:
                        return True
    return False

def charge_phase(board, player_units):
    print("\n--- Charge Phase ---")

    for unit in player_units:
        if unit.has_run:
            print(f"{unit.name} ran this turn and cannot charge.")
            continue

        if not is_near_enemy(unit, board, within_inches=12):
            print(f"{unit.name} is too far from any enemy to charge.")
            continue

        print(f"{unit.name} is eligible to charge.")
        choice = input("Attempt charge? (Y/N): ").strip().lower()
        if choice not in ["y", "yes"]:
            print(f"{unit.name} skips charging.")
            continue

        charge_roll = random.randint(1, 6) + random.randint(1, 6)
        max_distance_squares = charge_roll * 2
        print(f"Rolled a charge distance of {charge_roll} inches.")

        # Find chargeable enemy units
        charge_targets = []
        listed_units = []

        for enemy_unit in board.units:
            if enemy_unit.team != unit.team:
                for model in enemy_unit.models:
                    for friendly_model in unit.models:
                        dist = math.sqrt((friendly_model.x - model.x)**2 + (friendly_model.y - model.y)**2)
                        if dist <= max_distance_squares:
                            if enemy_unit not in listed_units:
                                listed_units.append(enemy_unit)
                            break

        if not listed_units:
            print("No valid targets in range.")
            continue

        print("You may charge the following enemy units:")
        for i, enemy_unit in enumerate(listed_units):
            print(f"{i + 1}. {enemy_unit.name}")

        try:
            selection = int(input("Select target unit number: ").strip()) - 1
            target_unit = listed_units[selection]
        except (ValueError, IndexError):
            print("Invalid selection.")
            continue

        # Find closest model in that unit
        closest_model = None
        closest_dist = float("inf")
        for model in target_unit.models:
            dist = math.sqrt((unit.x - model.x)**2 + (unit.y - model.y)**2)
            if dist < closest_dist:
                closest_model = model
                closest_dist = dist

        if closest_model is None:
            print("No valid target model found.")
            continue

        # Determine a destination 1 square away from the target model
        dx = closest_model.x - unit.x
        dy = closest_model.y - unit.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist == 0:
            print("Target model is on top of your model. Charge fails.")
            continue

        dx /= dist
        dy /= dist

        dest_x = closest_model.x - int(round(dx * 1))  # Stop 1 square (~0.5") away
        dest_y = closest_model.y - int(round(dy * 1))

        if not (0 <= dest_x < board.width and 0 <= dest_y < board.height):
            print("Proposed charge destination is out of bounds.")
            continue

        # Check for blocked path
        path = board.get_path(unit.x, unit.y, dest_x, dest_y)
        blocked, blocked_tile = board.is_path_blocked(path, (unit.x, unit.y), unit)
        if blocked:
            print(f"Charge path is blocked at {blocked_tile}. Charge fails.")
            continue

        print(f"Proposed charge destination: ({dest_x}, {dest_y})")
        accept = input("Accept this charge? (Y/N): ").strip().lower()
        if accept not in ["y", "yes"]:
            print("Charge cancelled.")
            continue

        success = board.move_unit(unit, dest_x, dest_y, confirm=True)
        if success:
            print(f"{unit.name} successfully charged {target_unit.name}!")
        else:
            print("Charge failed during move.")

def ai_charge_phase(board, ai_units, player_units):
    print("\n--- AI Charge Phase ---")

    for unit in ai_units:
        if unit.has_run:
            print(f"{unit.name} ran this turn and cannot charge.")
            continue

        if not is_near_enemy(unit, board, within_inches=12):
            print(f"{unit.name} is too far from enemy units to charge.")
            continue

        charge_roll = random.randint(1, 6) + random.randint(1, 6)
        max_distance_squares = charge_roll * 2
        print(f"{unit.name} rolls a {charge_roll} for charge distance.")

        # Find closest player model within range
        closest_enemy = None
        closest_dist = float("inf")
        for enemy_unit in player_units:
            for model in enemy_unit.models:
                dist = math.sqrt((unit.x - model.x)**2 + (unit.y - model.y)**2)
                if dist <= max_distance_squares and dist < closest_dist:
                    closest_dist = dist
                    closest_enemy = model

        if not closest_enemy:
            print(f"{unit.name} found no target within {charge_roll} inches.")
            continue

        # Charge destination: 1 square away from enemy
        dx = closest_enemy.x - unit.x
        dy = closest_enemy.y - unit.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist == 0:
            print(f"{unit.name} is standing on the enemy? Charge skipped.")
            continue

        dx /= dist
        dy /= dist

        dest_x = closest_enemy.x - int(round(dx * 1))
        dest_y = closest_enemy.y - int(round(dy * 1))

        if not (0 <= dest_x < board.width and 0 <= dest_y < board.height):
            print(f"{unit.name}'s charge destination is out of bounds.")
            continue

        # Check path is clear
        path = board.get_path(unit.x, unit.y, dest_x, dest_y)
        blocked, blocked_tile = board.is_path_blocked(path, (unit.x, unit.y), unit)
        if blocked:
            print(f"{unit.name}'s charge path is blocked at {blocked_tile}.")
            continue

        success = board.move_unit(unit, dest_x, dest_y)
        if success:
            print(f"{unit.name} successfully charged to ({dest_x}, {dest_y}).")
        else:
            print(f"{unit.name}'s charge failed during movement.")
