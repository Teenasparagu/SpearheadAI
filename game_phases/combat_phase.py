# game_logic/combat_phase.py
import math
from game_logic.units import is_in_combat

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

def resolve_melee_attacks(unit, enemy_units, log):
    log(f"{unit.name} makes melee attacks against nearby enemies!")
    # This is where you would add weapon stats and combat resolution later.

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

        already_fought.add(unit)

        active_team, inactive_team = inactive_team, active_team

    log(">> Combat Phase Ends.\n")
