import random
import math

def is_unit_in_combat(unit, enemy_units):
    for model in unit.models:
        for enemy_unit in enemy_units:
            for enemy_model in enemy_unit.models:
                distance = math.sqrt((model.x - enemy_model.x) ** 2 + (model.y - enemy_model.y) ** 2)
                if distance <= 3:
                    return True
    return False

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
    return 1  # Fallback

def shooting_phase(board, shooting_units, enemy_units):
    for unit in shooting_units:
        print(f"\nShooting Phase for {unit.name} (Team {unit.team})")

        in_combat = is_unit_in_combat(unit, enemy_units)
        attacks = unit.attacks if hasattr(unit, 'attacks') else []

        if not attacks:
            print(f"{unit.name} has no ranged attacks.")
            continue

        for model in unit.models:
            for weapon in attacks:
                if in_combat and "shoot_in_combat" not in weapon.get("keywords", []):
                    print(f"{unit.name} is in combat and cannot shoot with {weapon['name']}.")
                    continue

                # Find valid targets in range and line of sight
                valid_targets = []
                for enemy_unit in enemy_units:
                    for target_model in enemy_unit.models:
                        dx = target_model.x - model.x
                        dy = target_model.y - model.y
                        distance = math.sqrt(dx ** 2 + dy ** 2)
                        if distance <= weapon["range"]:
                            if board.is_path_clear(model.x, model.y, target_model.x, target_model.y):
                                valid_targets.append((enemy_unit, target_model))

                if not valid_targets:
                    print(f"No valid targets for {unit.name}'s {weapon['name']} from model at ({model.x}, {model.y}).")
                    continue

                # Choose the first target for now (can be expanded later)
                target_unit, target_model = valid_targets[0]
                print(f"{unit.name} at ({model.x}, {model.y}) shoots {weapon['name']} at {target_unit.name} at ({target_model.x}, {target_model.y})")

                for _ in range(weapon["attacks"]):
                    hit_roll = random.randint(1, 6)
                    if hit_roll >= weapon["to_hit"]:
                        wound_roll = random.randint(1, 6)
                        if wound_roll >= weapon["to_wound"]:
                            save_value = getattr(target_unit, "save", 4)  # Default 4+ save
                            save_roll = random.randint(1, 6)
                            if save_roll >= (save_value + weapon["rend"]):
                                print("Target saved the wound!")
                            else:
                                ward_value = getattr(target_unit, "ward", None)
                                if ward_value:
                                    ward_roll = random.randint(1, 6)
                                    if ward_roll >= ward_value:
                                        print("Ward save successful!")
                                        continue

                                damage = roll_damage(weapon["damage"])
                                print(f"{damage} damage dealt to {target_unit.name}!")

                                for _ in range(damage):
                                    for target in target_unit.models:
                                        if not hasattr(target, 'wounds'):  # Create wound attr if needed
                                            target.wounds = 0

                                    # Assign to first model with < 1 wound (or continue damage spillover)
                                    for model in target_unit.models:
                                        if getattr(model, 'wounds', 0) < 1:
                                            model.wounds += 1
                                            print(f"Damage assigned to model at ({model.x}, {model.y})")
                                            if model.wounds >= 1:
                                                print(f"Model at ({model.x}, {model.y}) slain!")
                                                target_unit.models.remove(model)
                                            break

                        else:
                            print("Failed to wound.")
                    else:
                        print("Missed.")