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


def _distance_between_units(a, b):
    min_dist = float("inf")
    for m in a.models:
        for e in b.models:
            d = math.sqrt((m.x - e.x) ** 2 + (m.y - e.y) ** 2)
            if d < min_dist:
                min_dist = d
    return min_dist


def _targets_in_range(unit, enemies, max_dist=3):
    res = []
    for enemy in enemies:
        if _distance_between_units(unit, enemy) <= max_dist:
            res.append(enemy)
    return res


def resolve_melee_attacks(unit, enemy_units, log, target=None):
    """Resolve melee attacks from ``unit`` against ``target`` or the nearest enemy."""
    if target is None:
        target, distance = _nearest_enemy(unit, enemy_units)
    else:
        distance = _distance_between_units(unit, target)
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

def _alternate_fights(board, enemy_map, units_by_team, start_team, get_input, log):
    """Alternate activations between teams for the given ``units_by_team``."""
    active = start_team
    inactive = 2 if start_team == 1 else 1
    while units_by_team[1] or units_by_team[2]:
        team_units = units_by_team[active]
        if not team_units:
            active, inactive = inactive, active
            continue

        if active == 1:
            # player chooses the unit
            while True:
                log("\nUnits available to fight:")
                for idx, u in enumerate(team_units, 1):
                    log(f"{idx}. {u.name}")
                resp = get_input("Choose a unit to fight (number): ").strip()
                try:
                    choice = int(resp)
                except (ValueError, TypeError):
                    choice = 1
                if 1 <= choice <= len(team_units):
                    unit = team_units.pop(choice - 1)
                    break
                log("Invalid selection.")
        else:
            unit = team_units.pop(0)

        if not unit.models:
            continue

        log(f"\n{unit.name} (Team {unit.team}) activates!")
        pile_in(board, unit, enemy_map[unit.team])

        # choose target
        targets = _targets_in_range(unit, enemy_map[unit.team])
        target = None
        if not targets:
            log("No enemies in melee range.")
        else:
            if active == 1 and len(targets) > 1:
                while True:
                    log("Targets in range:")
                    for idx, t in enumerate(targets, 1):
                        log(f"{idx}. {t.name}")
                    resp = get_input("Choose target (number): ").strip()
                    try:
                        t_choice = int(resp)
                    except (ValueError, TypeError):
                        t_choice = 1
                    if 1 <= t_choice <= len(targets):
                        target = targets[t_choice - 1]
                        break
                    log("Invalid selection.")
            else:
                # AI or only one target
                target, _ = _nearest_enemy(unit, enemy_map[unit.team])

        if target:
            resolve_melee_attacks(unit, enemy_map[unit.team], log, target=target)

        active, inactive = inactive, active


def combat_phase(board, current_team, player_units, ai_units, get_input, log):
    enemy_map = {1: ai_units, 2: player_units}

    all_units = {
        1: get_eligible_combat_units(player_units, board),
        2: get_eligible_combat_units(ai_units, board),
    }

    def _filter(keyword, negate=False):
        res = {
            1: [],
            2: [],
        }
        for team, units in all_units.items():
            for u in units:
                has_kw = keyword in u.keywords
                if (has_kw and not negate) or (negate and not has_kw):
                    res[team].append(u)
        return res

    strike_first = _filter("strike_first")
    strike_last = _filter("strike_last")
    normal = {
        1: [u for u in all_units[1] if u not in strike_first[1] and u not in strike_last[1]],
        2: [u for u in all_units[2] if u not in strike_first[2] and u not in strike_last[2]],
    }

    log("\n>> Combat Phase Begins!")
    log("Resolving combat abilities... (placeholder)")

    _alternate_fights(board, enemy_map, strike_first, current_team, get_input, log)
    _alternate_fights(board, enemy_map, normal, current_team, get_input, log)
    _alternate_fights(board, enemy_map, strike_last, current_team, get_input, log)

    log(">> Combat Phase Ends.\n")
