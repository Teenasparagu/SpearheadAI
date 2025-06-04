import random
import math


def is_valid_shooting_target(shooter, target, board, max_range=24):
    for shooter_model in shooter.models:
        for target_model in target.models:
            dx = target_model.x - shooter_model.x
            dy = target_model.y - shooter_model.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance <= max_range:
                if board.is_path_clear(shooter_model.x, shooter_model.y, target_model.x, target_model.y):
                    return True
    return False

def get_player_units_that_can_shoot(player_units, ai_units, board):
    eligible = []
    for unit in player_units:
        if not unit.models or not hasattr(unit, "ranged_weapons"):
            continue
        for enemy in ai_units:
            if is_valid_shooting_target(unit, enemy, board):
                eligible.append(unit)
                break
    return eligible

def list_targets_for_unit(unit, ai_units, board):
    targets = []
    for enemy in ai_units:
        if is_valid_shooting_target(unit, enemy, board):
            targets.append(enemy)
    return targets

def player_shooting_phase(board, player_units, ai_units, get_input, log):
    log("\n--- Shooting Phase (Player) ---")
    remaining_units = get_player_units_that_can_shoot(player_units, ai_units, board)

    while remaining_units:
        log("\nUnits available to shoot:")
        for idx, unit in enumerate(remaining_units):
            log(f"{idx + 1}. {unit.name} (at {unit.x}, {unit.y})")

        try:
            choice = int(get_input("Choose a unit to shoot with (number), or 0 to skip shooting: ")) - 1
        except ValueError:
            log("Invalid input.")
            continue

        if choice == -1:
            log("You skipped shooting with the remaining units.")
            break

        if 0 <= choice < len(remaining_units):
            shooting_unit = remaining_units[choice]
            targets = list_targets_for_unit(shooting_unit, ai_units, board)

            if not targets:
                log("No valid targets in range or line of sight.")
                remaining_units.remove(shooting_unit)
                continue

            log("\nAvailable targets:")
            for i, target in enumerate(targets):
                log(f"{i + 1}. {target.name} at ({target.x}, {target.y})")

            try:
                target_idx = int(get_input("Choose a target (number): ")) - 1
            except ValueError:
                log("Invalid input.")
                continue

            if 0 <= target_idx < len(targets):
                target = targets[target_idx]
                confirm = get_input(f"Confirm shooting {target.name}? (y/n): ").strip().lower()
                if confirm == 'y':
                    resolve_ranged_attacks(shooting_unit, target, board, log)
                    remaining_units.remove(shooting_unit)
                else:
                    log("Cancelled. Returning to unit selection.")
            else:
                log("Invalid target.")
        else:
            log("Invalid choice.")


def roll_damage(damage_value):
    if isinstance(damage_value, int):
        return damage_value
    if isinstance(damage_value, str):
        if damage_value.upper() == "D3":
            return random.randint(1, 3)
        elif damage_value.upper() == "D6":
            return random.randint(1, 6)
        elif damage_value.upper() == "2D3":
            return random.randint(1, 3) + random.randint(1, 3)
        elif damage_value.upper() == "2D6":
            return random.randint(1, 6) + random.randint(1, 6)
    return 1

def resolve_ranged_attacks(unit, target_unit, board, log):
    if not hasattr(unit, "ranged_weapons") or not unit.ranged_weapons:
        log(f"{unit.name} has no ranged weapons!")
        return

    log(f"\n{unit.name} is shooting at {target_unit.name}!")

    for weapon in unit.ranged_weapons:
        log(f"Using {weapon['name']}:")

        for model in unit.models:
            for _ in range(weapon["attacks"]):
                hit = random.randint(1, 6)
                log(f"  Rolled to hit: {hit} (needs {weapon['to_hit']}+)")

                if hit >= weapon["to_hit"]:
                    wound = random.randint(1, 6)
                    log(f"  Rolled to wound: {wound} (needs {weapon['to_wound']}+)")

                    if wound >= weapon["to_wound"]:
                        damage = weapon["damage"]
                        enemy_model = target_unit.models[0] if target_unit.models else None
                        if enemy_model:
                            log(f"  {damage} damage dealt to model at ({enemy_model.x}, {enemy_model.y})")
                            target_unit.apply_damage(damage)
                        else:
                            log("  No targets left in unit!")
                    else:
                        log("  Failed to wound.")
                else:
                    log("  Missed.")
