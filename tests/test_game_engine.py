import os
import sys
import builtins
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_logic.game_engine import run_deployment_phase, GameEngine


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


def _simple_deploy_units(board, units, territory, zone_name, player_label, get_input, log):
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


def setup_deployment(monkeypatch):
    engine = GameEngine()
    logs, log = _collect_log()
    get_input = _fake_input_generator(["first"])

    monkeypatch.setattr("game_logic.game_engine.choose_faction", lambda gi, lg: "stormcast")
    monkeypatch.setattr("game_logic.game_engine.roll_off", lambda: ("player", "ai"))
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
    engine, _ = setup_deployment(monkeypatch)
    unit = engine.game_state.units["player"][0]
    start = (unit.x, unit.y)
    engine.board.move_unit(unit, unit.x + 1, unit.y)
    assert (unit.x, unit.y) != start
