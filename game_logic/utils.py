
def _simple_deploy_units(board, units, territory, zone_name, player_label, get_input=None, log=lambda *a, **k: None):
    """Simplified unit placement used for web UI and tests."""
    for idx, unit in enumerate(units):
        if player_label.lower() == "player":
            unit.x = 1
            unit.y = 1 + idx * 10
        else:
            unit.x = board.width - 2
            unit.y = board.height - 2 - idx * 10
        for model in unit.models:
            dx = unit.x - unit.models[0].x
            dy = unit.y - unit.models[0].y
            model.x += dx
            model.y += dy
        board.place_unit(unit)


def within_enemy_buffer(x, y, enemy_zone, buffer=12):
    """Check if a coordinate is within the buffer distance of the enemy territory."""
    for ex, ey in enemy_zone:
        if ((x - ex) ** 2 + (y - ey) ** 2) ** 0.5 < buffer:
            return True
    return False


def valid_model_position(model, board, enemy_zone, placed):
    """Check if a model can be placed at its current coords."""
    from game_logic.board import TILE_EMPTY

    for x, y in model.get_occupied_squares():
        if not (0 <= x < board.width and 0 <= y < board.height):
            return False
        if board.grid[y][x] != TILE_EMPTY:
            return False

    if within_enemy_buffer(model.x, model.y, enemy_zone):
        return False

    if placed:
        import math
        if not any(math.hypot(model.x - p.x, model.y - p.y) <= 2 for p in placed):
            return False
    return True

