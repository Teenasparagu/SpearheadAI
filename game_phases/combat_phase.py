# game_logic/combat_phase.py
import math

def is_in_combat(unit, enemy_units):
    for model in unit.models:
        for enemy in enemy_units:
            for enemy_model in enemy.models:
                distance = math.sqrt((model.x - enemy_model.x) ** 2 + (model.y - enemy_model.y) ** 2)
                if distance <= 6:  # 3 inches = 6 tiles
                    return True
    return False

def get_eligible_combat_units(units, enemies):
    return [unit for unit in units if is_in_combat(unit, enemies)]

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

def resolve_melee_attacks(unit, enemy_units):
    print(f"{unit.name} makes melee attacks against nearby enemies!")
    # This is where you would add weapon stats and combat resolution later.

def combat_phase(board, current_team, player_units, ai_units):
    all_units = player_units + ai_units
    enemy_map = {1: ai_units, 2: player_units}
    team_map = {1: player_units, 2: ai_units}

    eligible_units = {
        1: get_eligible_combat_units(player_units, ai_units),
        2: get_eligible_combat_units(ai_units, player_units)
    }

    already_fought = set()
    active_team = current_team
    inactive_team = 2 if current_team == 1 else 1

    print("\n>> Combat Phase Begins!")

    while eligible_units[1] or eligible_units[2]:
        team_units = eligible_units[active_team]
        if not team_units:
            active_team, inactive_team = inactive_team, active_team
            continue

        unit = team_units.pop(0)

        print(f"\n{unit.name} (Team {unit.team}) activates!")

        pile_in(board, unit, enemy_map[unit.team])
        resolve_melee_attacks(unit, enemy_map[unit.team])

        already_fought.add(unit)

        active_team, inactive_team = inactive_team, active_team

    print(">> Combat Phase Ends.\n")