import math
import random


def _place_model_near(board, unit, model_idx: int, target_x: int, target_y: int,
                      max_dist: int, log, *, enforce_coherency: bool = True) -> bool:
    """Attempt to place ``model_idx`` near ``target_x, target_y``.

    Searches outward one square at a time until a valid location is found that
    does not exceed ``max_dist`` from the model's starting position.
    Returns ``True`` if the model is successfully placed.
    """
    start_x = unit.models[model_idx].x
    start_y = unit.models[model_idx].y

    for radius in range(max_dist + 1):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x = target_x + dx
                y = target_y + dy
                if math.sqrt((x - start_x) ** 2 + (y - start_y) ** 2) > max_dist:
                    continue
                if not (0 <= x < board.width and 0 <= y < board.height):
                    continue
                if board.move_model(unit, model_idx, x, y,
                                    enforce_coherency=enforce_coherency):
                    return True
    return False

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

def charge_phase(board, player_units, get_input, log):
    log("\n--- Charge Phase ---")

    for unit in player_units:
        if unit.has_run:
            log(f"{unit.name} ran this turn and cannot charge.")
            continue

        if not is_near_enemy(unit, board, within_inches=12):
            log(f"{unit.name} is too far from any enemy to charge.")
            continue

        log(f"{unit.name} is eligible to charge.")
        choice = get_input("Attempt charge? (Y/N): ").strip().lower()
        if choice not in ["y", "yes"]:
            log(f"{unit.name} skips charging.")
            continue

        charge_roll = random.randint(1, 6) + random.randint(1, 6)
        max_distance_squares = charge_roll * 2
        log(f"Rolled a charge distance of {charge_roll} inches.")

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
            log("No valid targets in range.")
            continue

        log("You may charge the following enemy units:")
        for i, enemy_unit in enumerate(listed_units):
            log(f"{i + 1}. {enemy_unit.name}")

        try:
            selection = int(get_input("Select target unit number: ").strip()) - 1
            target_unit = listed_units[selection]
        except (ValueError, IndexError):
            log("Invalid selection.")
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
            log("No valid target model found.")
            continue

        # Determine a destination 1 square away from the target model
        dx = closest_model.x - unit.x
        dy = closest_model.y - unit.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist == 0:
            log("Target model is on top of your model. Charge fails.")
            continue

        def _sgn(val: float) -> int:
            if val > 0:
                return 1
            if val < 0:
                return -1
            return 0

        # Move toward the target along the approach vector
        dest_x = closest_model.x - _sgn(dx)
        dest_y = closest_model.y - _sgn(dy)

        if not (0 <= dest_x < board.width and 0 <= dest_y < board.height):
            log("Proposed charge destination is out of bounds.")
            continue

        # Check for blocked path
        path = board.get_path(unit.x, unit.y, dest_x, dest_y)
        blocked, blocked_tile = board.is_path_blocked(path, (unit.x, unit.y), unit)
        if blocked:
            log(f"Charge path is blocked at {blocked_tile}. Charge fails.")
            continue

        log(f"Proposed charge destination: ({dest_x}, {dest_y})")
        accept = get_input("Accept this charge? (Y/N): ").strip().lower()
        if accept not in ["y", "yes"]:
            log("Charge cancelled.")
            continue

        auto = get_input("Let the computer place models automatically? (Y/N): ")
        auto = auto.strip().lower()

        original_pos = [(m.x, m.y) for m in unit.models]

        if auto in ["y", "yes", "a", "auto"]:
            success = board.move_unit(unit, dest_x, dest_y)
            if not success:
                log("Destination occupied! Attempting individual placement...")
                dx_total = dest_x - unit.x
                dy_total = dest_y - unit.y
                success = True
                for idx, m in enumerate(unit.models):
                    tx = original_pos[idx][0] + dx_total
                    ty = original_pos[idx][1] + dy_total
                    if not _place_model_near(board, unit, idx, tx, ty,
                                             int(max_distance_squares), log,
                                             enforce_coherency=False):
                        success = False
                        break
            if success:
                if not board.units_base_to_base(unit, target_unit):
                    success = False
                    log("Charge must end base-to-base with the target.")

            if success and board.models_overlap():
                success = False
                log("Charge results in overlapping models.")

            if success:
                confirm = get_input(
                    "Are all model locations acceptable? (Y/N): "
                ).strip().lower()
                if confirm in ["y", "yes"]:
                    log(f"{unit.name} successfully charged {target_unit.name}!")
                else:
                    for i, (ox, oy) in enumerate(original_pos):
                        board.move_model(unit, i, ox, oy)
                    log("Charge cancelled.")
            else:
                for i, (ox, oy) in enumerate(original_pos):
                    board.move_model(unit, i, ox, oy)
                log("Charge failed during move.")
        else:
            success = True
            for idx, m in enumerate(unit.models):
                label = "Leader" if idx == 0 else f"Model {idx}"
                while True:
                    resp = get_input(
                        f"Enter destination for {label} as 'x y': "
                    ).strip().lower()
                    try:
                        x_str, y_str = resp.split()
                        tx = int(x_str)
                        ty = int(y_str)
                    except ValueError:
                        log("Invalid input format. Use 'x y'.")
                        continue
                    if math.sqrt(
                        (tx - original_pos[idx][0]) ** 2
                        + (ty - original_pos[idx][1]) ** 2
                    ) > max_distance_squares:
                        log("That position is beyond the charge distance.")
                        continue
                    if board.move_model(unit, idx, tx, ty,
                                       enforce_coherency=False):
                        break
                    log("Position invalid. Searching nearby...")
                    if _place_model_near(
                        board, unit, idx, tx, ty,
                        int(max_distance_squares), log,
                        enforce_coherency=False
                    ):
                        break
                    log("Unable to place model. Try again.")
            if success:
                if not board.units_base_to_base(unit, target_unit):
                    success = False
                    log("Charge must end base-to-base with the target.")

            if success and board.models_overlap():
                success = False
                log("Charge results in overlapping models.")

            if success:
                confirm = get_input(
                    "Are all model locations acceptable? (Y/N): "
                ).strip().lower()
                if confirm not in ["y", "yes"]:
                    for i, (ox, oy) in enumerate(original_pos):
                        board.move_model(unit, i, ox, oy)
                    log("Charge cancelled.")
                else:
                    log(f"{unit.name} successfully charged {target_unit.name}!")
            else:
                for i, (ox, oy) in enumerate(original_pos):
                    board.move_model(unit, i, ox, oy)
                log("Charge cancelled.")

def ai_charge_phase(board, ai_units, player_units, get_input, log):
    log("\n--- AI Charge Phase ---")

    for unit in ai_units:
        if unit.has_run:
            log(f"{unit.name} ran this turn and cannot charge.")
            continue

        if not is_near_enemy(unit, board, within_inches=12):
            log(f"{unit.name} is too far from enemy units to charge.")
            continue

        charge_roll = random.randint(1, 6) + random.randint(1, 6)
        max_distance_squares = charge_roll * 2
        log(f"{unit.name} rolls a {charge_roll} for charge distance.")

        # Find closest player model within range
        closest_enemy = None
        closest_enemy_unit = None
        closest_dist = float("inf")
        for enemy_unit in player_units:
            for model in enemy_unit.models:
                dist = math.sqrt((unit.x - model.x)**2 + (unit.y - model.y)**2)
                if dist <= max_distance_squares and dist < closest_dist:
                    closest_dist = dist
                    closest_enemy = model
                    closest_enemy_unit = enemy_unit

        if not closest_enemy:
            log(f"{unit.name} found no target within {charge_roll} inches.")
            continue

        # Charge destination: 1 square away from enemy
        dx = closest_enemy.x - unit.x
        dy = closest_enemy.y - unit.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist == 0:
            log(f"{unit.name} is standing on the enemy? Charge skipped.")
            continue

        dx /= dist
        dy /= dist

        dest_x = closest_enemy.x - int(round(dx * 1))
        dest_y = closest_enemy.y - int(round(dy * 1))

        if not (0 <= dest_x < board.width and 0 <= dest_y < board.height):
            log(f"{unit.name}'s charge destination is out of bounds.")
            continue

        # Check path is clear
        path = board.get_path(unit.x, unit.y, dest_x, dest_y)
        blocked, blocked_tile = board.is_path_blocked(path, (unit.x, unit.y), unit)
        if blocked:
            log(f"{unit.name}'s charge path is blocked at {blocked_tile}.")
            continue

        success = board.move_unit(unit, dest_x, dest_y)
        if success and not board.units_base_to_base(unit, closest_enemy_unit):
            success = False
        if success and board.models_overlap():
            success = False

        if success:
            log(f"{unit.name} successfully charged to ({dest_x}, {dest_y}).")
        else:
            log(f"{unit.name}'s charge failed during movement.")
