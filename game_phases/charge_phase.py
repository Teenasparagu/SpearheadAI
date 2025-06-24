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


def ai_charge_phase(board, ai_units, player_units, get_input, log):
    """AI skips charging for now."""
    log("\n--- AI Charge Phase ---")
    for unit in ai_units:
        log(f"{unit.name} does not charge.")

def charge_phase(board, player_units, get_input, log):
    """Handle the player's charge phase with manual placement only."""
    log("\n--- Charge Phase ---")

    remaining = [u for u in player_units if not u.has_run]
    while remaining:
        log("Units able to charge:")
        for i, unit in enumerate(remaining, 1):
            log(f"{i}. {unit.name}")
        log("0. Done")
        try:
            choice = int(get_input("Select unit to charge (0 to finish): ").strip())
        except ValueError:
            log("Invalid selection.")
            continue
        if choice == 0:
            break
        if choice < 1 or choice > len(remaining):
            log("Invalid selection.")
            continue
        unit = remaining.pop(choice - 1)

        charge_roll = random.randint(1, 6) + random.randint(1, 6)
        log(f"Rolled a charge distance of {charge_roll} inches.")
        max_distance_squares = charge_roll * 2

        if not is_near_enemy(unit, board, within_inches=charge_roll):
            log("No enemy units within charge range.")
            continue

        original_pos = [(m.x, m.y) for m in unit.models]

        while True:
            aborted = False
            for idx, _ in enumerate(unit.models):
                label = "Leader" if idx == 0 else f"Model {idx}"
                while True:
                    resp = get_input(
                        f"Enter destination for {label} as 'x y' or 'cancel': "
                    ).strip().lower()
                    if resp == "cancel":
                        aborted = True
                        break
                    try:
                        x_str, y_str = resp.split()
                        tx = int(x_str)
                        ty = int(y_str)
                    except ValueError:
                        log("Invalid input format. Use 'x y' or 'cancel'.")
                        continue
                    if math.sqrt(
                        (tx - original_pos[idx][0]) ** 2
                        + (ty - original_pos[idx][1]) ** 2
                    ) > max_distance_squares:
                        log("That position is beyond the charge distance.")
                        continue
                    if board.move_model(unit, idx, tx, ty, enforce_coherency=False):
                        break
                    log("Position invalid. Try again.")
                if aborted:
                    break
            if aborted:
                for i, (ox, oy) in enumerate(original_pos):
                    board.move_model(unit, i, ox, oy, enforce_coherency=False)
                log("Charge cancelled.")
                break

            in_range = False
            for enemy_unit in board.units:
                if enemy_unit.team != unit.team:
                    if board.units_base_to_base(unit, enemy_unit):
                        in_range = True
                        break
            if not in_range:
                log("Charge must end within 1 square of an enemy unit.")
                for i, (ox, oy) in enumerate(original_pos):
                    board.move_model(unit, i, ox, oy, enforce_coherency=False)
                continue

            log(f"{unit.name} successfully charged!")
            break
