import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_logic.board import Board
from game_phases.deployment import deploy_terrain


def test_ai_terrain_failure_logs_reason(monkeypatch):
    board = Board()
    zone = [(x, y) for x in range(board.width) for y in range(board.height)]
    logs = []
    def log(msg):
        logs.append(msg)
    # Force invalid placements
    monkeypatch.setattr('game_phases.deployment.is_valid_terrain_placement', lambda *a, **k: (False, (0, 0)))
    deploy_terrain(board, team=2, zone=zone, enemy_zone=[], get_input=lambda _: "", log=log)
    assert any("Last error" in l for l in logs)
