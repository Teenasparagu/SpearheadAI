import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_logic.board import Board
from game_phases.deployment import get_deployment_zones


def test_straight_zones_touch():
    board = Board()
    defender_zone, attacker_zone = get_deployment_zones(board, "straight")
    mid = board.height // 2

    assert defender_zone(0, mid - 1)
    assert attacker_zone(0, mid)

    for x in range(board.width):
        for y in range(board.height):
            d = defender_zone(x, y)
            a = attacker_zone(x, y)
            assert d != a
            assert d or a


def test_diagonal_zones_touch():
    board = Board()
    defender_zone, attacker_zone = get_deployment_zones(board, "diagonal")

    for x in range(board.width):
        for y in range(board.height):
            d = defender_zone(x, y)
            a = attacker_zone(x, y)
            assert d != a
            assert d or a
