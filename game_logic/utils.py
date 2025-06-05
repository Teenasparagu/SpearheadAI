
def _simple_deploy_units(board, units, territory, enemy_territory, zone_name, player_label, get_input=None, log=lambda *a, **k: None):
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


def _triangle_offsets(size: int = 3):
    """Return coordinate offsets forming a right triangle of the given size."""
    offsets = []
    for y in range(size):
        for x in range(y + 1):
            offsets.append((x, y))
    return offsets

