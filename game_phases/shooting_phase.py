import random
import math
from game_logic.units import is_in_combat

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

def shooting_phase(board, shooting_units, enemy_units):
    for unit in shooting_units:
        print(f"\nShooting Phase for {unit.name} (Team {unit.team})")

        in_combat = any(is_in_combat(model.x, model.y, board, unit.team) for model in unit.models)

        for model in unit.models:
            attacks = getattr(model, 'ranged_attacks', [])
            if not attacks:
                continue

            for weapon in attacks:
                if in_combat and "shoot_in_combat" not in [k.lower() for k in weapon.get("keywords", [])]:
                    print(f"{unit.name} is in combat and cannot shoot with {weapon['name']}.")
                    continue

                valid_targets = []
                for enemy_unit in enemy_units:
                    for target_model in enemy_unit.models:
                        dx = target_model.x - model.x
                        dy = target_model.y - model.y
                        distance = math.sqrt(dx ** 2 + dy ** 2)
                        if distance <= weapon["range"]:
                            path = board.get_path(model.x, model.y, target_model.x, target_model.y)
                            blocked, _ = board.is_path_blocked(path, (model.x, model.y), unit)
                            if not blocked:
                                valid_targets.append((enemy_unit, target_model))

                if not valid_targets:
                    print(f"No valid targets for {unit.name}'s {weapon['name']} from model at ({model.x}, {model.y}).")
                    continue

                if unit.team == 1:
                    unit_targets = {}
                    for enemy_unit, enemy_model in valid_targets:
                        unit_targets.setdefault(enemy_unit.name, []).append((enemy_unit, enemy_model))

                    print("\nChoose a target:")
                    for i, unit_name in enumerate(unit_targets.keys()):
                        print(f"{i + 1}. {unit_name}")

                    while True:
                        try:
                            choice = int(input("Enter number of the unit to shoot: ")) - 1
                            selected_name = list(unit_targets.keys())[choice]
                            break
                        except (ValueError, IndexError):
                            print("Invalid choice. Try again.")

                    selected_targets = unit_targets[selected_name]
                    target_unit, target_model = selected_targets[0]
                else:
                    target_unit, target_model = valid_targets[0]

                print(f"{unit.name} at ({model.x}, {model.y}) shoots {weapon['name']} at {target_unit.name} at ({target_model.x}, {target_model.y})")

                num_attacks = roll_damage(weapon["attacks"])

                for _ in range(num_attacks):
                    hit_roll = random.randint(1, 6)
                    auto_wound = "crit_auto_wound" in [k.lower() for k in weapon.get("keywords", [])] and hit_roll == 6

                    if hit_roll >= weapon["to_hit"] or auto_wound:
                        if not auto_wound:
                            wound_roll = random.randint(1, 6)
                            if wound_roll < weapon["to_wound"]:
                                print("Failed to wound.")
                                continue
                        else:
                            print("Critical hit! Auto-wound triggered.")

                        save_value = getattr(target_unit, "save", 4)
                        save_roll = random.randint(1, 6)
                        if save_roll >= (save_value + weapon["rend"]):
                            print("Target saved the wound!")
                            continue

                        ward_value = getattr(target_unit, "ward", None)
                        if ward_value:
                            ward_roll = random.randint(1, 6)
                            if ward_roll >= ward_value:
                                print("Ward save successful!")
                                continue

                        damage = roll_damage(weapon["damage"])
                        print(f"{damage} damage dealt to {target_unit.name}!")

                        for _ in range(damage):
                            if not hasattr(target_model, 'wounds'):
                                target_model.wounds = 0

                            target_model.wounds += 1
                            print(f"Damage assigned to model at ({target_model.x}, {target_model.y})")

                            if target_model.wounds >= getattr(target_unit, 'health', 1):
                                print(f"Model at ({target_model.x}, {target_model.y}) slain!")
                                if target_model in target_unit.models:
                                    target_unit.models.remove(target_model)
                                break
                    else:
                        print("Missed.")
