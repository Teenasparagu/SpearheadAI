# game_logic/combat_phase.py
import math
import random
from game_logic.units import is_in_combat
from game_phases.shooting_phase import roll_damage


def _apply_damage(unit, dmg, log):
    """Apply ``dmg`` wounds to ``unit`` logging the results."""
    for model in list(unit.models):
        if model.is_alive():
            model.take_damage(dmg)
            log(
                f"{unit.name}: Model took {dmg} damage (HP: {model.current_health}/{model.max_health})"
            )
            if not model.is_alive():
                log(f"{unit.name}: A model has been slain!")
                unit.models.remove(model)
            break
    log(f"{unit.name}: {len(unit.models)} model(s) remaining.")

def get_eligible_combat_units(units, board):
    return [
        unit
        for unit in units
        if any(is_in_combat(model.x, model.y, board, unit.team) for model in unit.models)
    ]

def pile_in(board, unit, enemies):
    for model in unit.models:
        closest = None
        min_distance = float("inf")
        for enemy in enemies:
            for enemy_model in enemy.models:
                distance = math.sqrt((enemy_model.x - model.x) ** 2 + (enemy_model.y - model.y) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    closest = enemy_model

        if closest and min_distance > 0:
            dx = closest.x - model.x
            dy = closest.y - model.y
            move_distance = min(6, min_distance)  # 3" = 6 tiles
            norm = math.sqrt(dx**2 + dy**2)
            step_x = round((dx / norm) * move_distance) if norm != 0 else 0
            step_y = round((dy / norm) * move_distance) if norm != 0 else 0
            new_x = model.x + step_x
            new_y = model.y + step_y
            if 0 <= new_x < board.width and 0 <= new_y < board.height:
                model.x = new_x
                model.y = new_y

def _nearest_enemy(unit, enemy_units):
    closest = None
    min_dist = float("inf")
    for enemy in enemy_units:
        for e_model in enemy.models:
            for model in unit.models:
                dist = math.sqrt((model.x - e_model.x) ** 2 + (model.y - e_model.y) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    closest = enemy
    return closest, min_dist


def resolve_melee_attacks(unit, enemy_units, log):
    """Resolve melee attacks from ``unit`` against the nearest enemy unit."""
    target, distance = _nearest_enemy(unit, enemy_units)
    if not target or distance > 3:
        log("No enemies in melee range.")
        return

    log(f"{unit.name} attacks {target.name}!")

    total_attacks = 0
    total_wounds = 0
    total_saves = 0
    total_damage = 0
    models_before = len(target.models)

    for weapon in unit.melee_weapons:
        log(f"Using {weapon['name']}:")
        for model in unit.models:
            for _ in range(weapon['attacks']):
                total_attacks += 1
                hit = random.randint(1, 6)
                log(f"  Hit roll: {hit} (needs {weapon['to_hit']}+)")
                if hit >= weapon['to_hit']:
                    wound = random.randint(1, 6)
                    log(f"  Wound roll: {wound} (needs {weapon['to_wound']}+)")
                    if wound >= weapon['to_wound']:
                        total_wounds += 1
                        save = random.randint(1, 6)
                        log(f"  Save roll: {save} (needs 4+)")
                        if save >= 4:
                            total_saves += 1
                            log("  Saved!")
                        else:
                            dmg = roll_damage(weapon['damage'])
                            total_damage += dmg
                            log(f"  {dmg} damage inflicted!")
                            for _ in range(dmg):
                                _apply_damage(target, 1, log)
                    else:
                        log("  Failed to wound.")
                else:
                    log("  Missed.")

    models_after = len(target.models)
    log(
        f"Attacks rolled: {total_attacks}, Wounds rolled: {total_wounds}, Saves made: {total_saves}"
    )
    log(
        f"{target.name} took {total_damage} wounds, {models_before - models_after} models died, {models_after} remain."
    )

def combat_phase(board, current_team, player_units, ai_units, get_input, log):
    enemy_map = {1: ai_units, 2: player_units}

    eligible_units = {
        1: get_eligible_combat_units(player_units, board),
        2: get_eligible_combat_units(ai_units, board)
    }

    already_fought = set()
    active_team = current_team
    inactive_team = 2 if current_team == 1 else 1

    log("\n>> Combat Phase Begins!")

    while eligible_units[1] or eligible_units[2]:
        team_units = eligible_units[active_team]
        if not team_units:
            active_team, inactive_team = inactive_team, active_team
            continue

        unit = team_units.pop(0)

        log(f"\n{unit.name} (Team {unit.team}) activates!")

        pile_in(board, unit, enemy_map[unit.team])
        resolve_melee_attacks(unit, enemy_map[unit.team], log)

        already_fought.add(id(unit))

        active_team, inactive_team = inactive_team, active_team

    log(">> Combat Phase Ends.\n")
