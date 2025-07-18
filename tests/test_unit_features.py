import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_logic.board import Board
from game_logic.units import Unit
from game_phases.deployment import get_deployment_zones, is_valid_unit_placement
from game_logic.factions.stormcast import StormcastFactory


def test_unit_deployment_respects_enemy_distance():
    board = Board()
    defender_zone, attacker_zone = get_deployment_zones(board, "straight")
    unit_data = StormcastFactory.unit_definitions["Liberators"]
    unit = Unit("Liberators", "stormcast", team=1, unit_data=unit_data)
    zone_coords = [(x, y) for x in range(board.width) for y in range(board.height) if defender_zone(x, y)]
    enemy_coords = [(x, y) for x in range(board.width) for y in range(board.height) if attacker_zone(x, y)]
    mid = board.height // 2
    valid, _ = is_valid_unit_placement(board.width // 2, mid - 1, unit, board, zone_coords, enemy_coords)
    assert valid


def test_move_model_coherency():
    board = Board()
    # create simple unit with small bases
    unit = Unit("Test", "stormcast", team=1, num_models=2, unit_data={"num_models":2,"move_range":6,"base_width":1.0,"base_height":1.0})
    board.place_unit(unit)
    assert not board.move_model(unit, 1, unit.models[0].x + 3, unit.models[0].y)
    assert board.move_model(unit, 1, unit.models[0].x + 2, unit.models[0].y)


def test_move_model_ignore_coherency():
    board = Board()
    unit = Unit("Test", "stormcast", team=1, num_models=2,
                unit_data={"num_models": 2, "move_range": 6,
                           "base_width": 1.0, "base_height": 1.0})
    board.place_unit(unit)
    # normally this would fail due to coherency
    assert board.move_model(unit, 1, unit.models[0].x + 3, unit.models[0].y,
                             enforce_coherency=False)


def test_triangle_offsets_coherent_placement():
    board = Board()
    unit = Unit(
        "Test",
        "stormcast",
        team=1,
        num_models=3,
        unit_data={"num_models": 3, "move_range": 6, "base_width": 1.0, "base_height": 1.0},
    )
    from app import _triangle_offsets

    offsets = _triangle_offsets(
        len(unit.models),
        orientation=1,
        base_width=unit.base_width,
        base_height=unit.base_height,
    )
    for i, (dx, dy) in enumerate(offsets):
        unit.models[i].x = unit.x + dx
        unit.models[i].y = unit.y + dy

    assert board.place_unit(unit)
    occupied = []
    for model in unit.models:
        occupied.extend(model.get_occupied_squares())
    assert len(occupied) == len(set(occupied))

