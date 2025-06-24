
def center_unit_on_leader_square(unit, center_x, center_y):
    """Shift ``unit`` so the leader's central square is at ``center_x, center_y``."""

    leader = unit.models[0]
    current_center = leader.get_central_square()
    dx = center_x - current_center[0]
    dy = center_y - current_center[1]

    for m in unit.models:
        m.x += dx
        m.y += dy

    unit.x += dx
    unit.y += dy


def center_model_on_square(model, center_x, center_y):
    """Move ``model`` so its central square is at ``center_x, center_y``."""

    current_center = model.get_central_square()
    dx = center_x - current_center[0]
    dy = center_y - current_center[1]
    model.x += dx
    model.y += dy


def _simple_deploy_units(board, units, territory, enemy_territory, zone_name, player_label, get_input=None, log=lambda *a, **k: None):
    """Simplified unit placement used for web UI and tests."""
    for idx, unit in enumerate(units):
        if player_label.lower() == "player":
            cx = 1
            cy = 1 + idx * 10
        else:
            cx = board.width - 2
            cy = board.height - 2 - idx * 10

        center_unit_on_leader_square(unit, cx, cy)
        board.place_unit(unit)


def _triangle_offsets(size: int = 3):
    """Return coordinate offsets forming a right triangle of the given size."""
    offsets = []
    for y in range(size):
        for x in range(y + 1):
            offsets.append((x, y))
    return offsets

