import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_logic.board import Board
from game_logic.units import Unit
from game_phases.deployment import (
    get_deployment_zones,
    is_valid_unit_placement,
    is_valid_model_position,
)
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

    offsets = _triangle_offsets(len(unit.models), orientation=1)
    for i, (dx, dy) in enumerate(offsets):
        unit.models[i].x = unit.x + dx
        unit.models[i].y = unit.y + dy

    assert board.place_unit(unit)


def test_model_position_and_unit_coherency():
    board = Board()
    defender_zone, attacker_zone = get_deployment_zones(board, "straight")
    zone_coords = [
        (x, y)
        for x in range(board.width)
        for y in range(board.height)
        if defender_zone(x, y)
    ]
    enemy_coords = [
        (x, y)
        for x in range(board.width)
        for y in range(board.height)
        if attacker_zone(x, y)
    ]
    unit = Unit(
        "Test",
        "stormcast",
        team=1,
        num_models=2,
        unit_data={"num_models": 2, "move_range": 6, "base_width": 1.0, "base_height": 1.0},
    )

    leader_x, leader_y = 5, 5
    ok, _ = is_valid_model_position(
        leader_x,
        leader_y,
        unit.models[0],
        board,
        zone_coords,
        enemy_coords,
        [],
    )
    assert ok

    ok, _ = is_valid_model_position(
        leader_x + 1,
        leader_y,
        unit.models[1],
        board,
        zone_coords,
        enemy_coords,
        [(leader_x, leader_y)],
    )
    assert ok

    ok, _ = is_valid_model_position(
        leader_x + 4,
        leader_y + 4,
        unit.models[1],
        board,
        zone_coords,
        enemy_coords,
        [(leader_x, leader_y)],
    )
    assert not ok

    unit.models[0].x = leader_x
    unit.models[0].y = leader_y
    unit.models[1].x = leader_x + 3
    unit.models[1].y = leader_y + 3
    unit.x, unit.y = leader_x, leader_y
    ok, _ = is_valid_unit_placement(unit.x, unit.y, unit, board, zone_coords, enemy_coords)
    assert not ok

    unit.models[1].x = leader_x + 1
    unit.models[1].y = leader_y
    ok, _ = is_valid_unit_placement(unit.x, unit.y, unit, board, zone_coords, enemy_coords)
    assert ok

