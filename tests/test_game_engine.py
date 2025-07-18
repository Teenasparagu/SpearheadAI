import os
import sys
import builtins
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_logic.game_engine import run_deployment_phase, GameEngine
from game_logic.utils import _simple_deploy_units


def _fake_input_generator(responses):
    responses = list(responses)
    def _inner(prompt):
        return responses.pop(0)
    return _inner


def _collect_log():
    logs = []
    def _log(msg):
        logs.append(msg)
    return logs, _log



def setup_deployment(monkeypatch):
    engine = GameEngine()
    logs, log = _collect_log()
    get_input = _fake_input_generator(["first"])

    monkeypatch.setattr("game_logic.game_engine.choose_faction", lambda gi, lg: "stormcast")
    monkeypatch.setattr("game_logic.game_engine.roll_off", lambda gi, lg: ("player", "ai"))
    monkeypatch.setattr("game_logic.game_engine.choose_battlefield", lambda gi, lg: "aqshy")
    monkeypatch.setattr("game_logic.game_engine.choose_deployment_map", lambda gi, lg: "straight")
    monkeypatch.setattr("game_logic.game_engine.deploy_terrain", lambda *a, **k: None)
    monkeypatch.setattr("game_logic.game_engine.deploy_units", _simple_deploy_units)
    monkeypatch.setattr("game_logic.game_engine.random.choice", lambda seq: seq[0])

    run_deployment_phase(engine.game_state, engine.board, get_input, log)
    return engine, logs


def test_run_deployment_phase(monkeypatch):
    engine, logs = setup_deployment(monkeypatch)

    assert engine.game_state.phase == "hero"
    assert engine.game_state.turn_order == ["player", "ai"]
    assert engine.game_state.units["player"]
    assert engine.game_state.units["ai"]
    assert any("Deployment phase complete." in l for l in logs)


def test_sample_turn_move(monkeypatch):
    # isolate a board with a single unit to avoid placement conflicts
    from game_logic.board import Board
    from game_logic.units import Unit
    from game_logic.factions.stormcast import StormcastFactory

    board = Board()
    unit = Unit("Liberators", "stormcast", team=1,
                unit_data=StormcastFactory.unit_definitions["Liberators"])
    board.place_unit(unit)

    start = [(m.x, m.y) for m in unit.models]
    moved = board.move_unit(unit, unit.x + 1, unit.y)
    assert moved
    delta = (1, 0)
    for (sx, sy), model in zip(start, unit.models):
        assert (model.x, model.y) == (sx + delta[0], sy + delta[1])
