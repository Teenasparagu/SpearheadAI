import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_logic.game_engine import GameEngine, run_deployment_phase
from game_logic.utils import _simple_deploy_units
from game_phases import movement_phase, shooting_phase, charge_phase, combat_phase


def _fake_input_generator(responses):
    responses = list(responses)
    def _inner(prompt):
        return responses.pop(0) if responses else ""
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


def test_movement_phase_skip(monkeypatch):
    engine, _ = setup_deployment(monkeypatch)
    original_positions = [(u.x, u.y) for u in engine.game_state.units["player"]]

    responses = []
    for _ in engine.game_state.units["player"]:
        responses.extend(["n", "skip"])
    get_input = _fake_input_generator(responses)

    movement_phase.player_movement_phase(engine.board, engine.game_state.units["player"], get_input, lambda *_: None)

    assert [(u.x, u.y) for u in engine.game_state.units["player"]] == original_positions


def test_shooting_phase_no_targets(monkeypatch):
    engine, _ = setup_deployment(monkeypatch)
    logs, log = _collect_log()
    get_input = _fake_input_generator(["0"])

    shooting_phase.player_shooting_phase(engine.board, engine.game_state.units["player"], engine.game_state.units["ai"], get_input, log)

    assert any("Shooting Phase" in l for l in logs)


def test_charge_phase_no_targets(monkeypatch):
    engine, _ = setup_deployment(monkeypatch)
    logs, log = _collect_log()
    responses = ["n"] * len(engine.game_state.units["player"])
    get_input = _fake_input_generator(responses)

    charge_phase.charge_phase(engine.board, engine.game_state.units["player"], get_input, log)

    assert any("Charge Phase" in l for l in logs)


def test_combat_phase_no_engagement(monkeypatch):
    engine, _ = setup_deployment(monkeypatch)
    logs, log = _collect_log()

    combat_phase.combat_phase(engine.board, current_team=1,
                              player_units=engine.game_state.units["player"],
                              ai_units=engine.game_state.units["ai"],
                              get_input=_fake_input_generator([]), log=log)

    assert any("Combat Phase Begins" in l for l in logs)
    assert any("Combat Phase Ends" in l for l in logs)


def test_charge_phase_calls_move_unit(monkeypatch):
    """Ensure ``charge_phase`` invokes ``Board.move_unit`` without unexpected
    parameters when a charge is accepted."""

    from game_logic.board import Board
    from game_logic.units import Unit
    from game_logic.factions.stormcast import StormcastFactory

    board = Board(width=20, height=20)

    player_unit = Unit(
        "Liberators", "stormcast", team=1,
        unit_data=StormcastFactory.unit_definitions["Liberators"],
    )
    board.place_unit(player_unit)

    enemy_unit = Unit(
        "Liberators", "stormcast", team=2,
        unit_data=StormcastFactory.unit_definitions["Liberators"],
    )
    # position enemy a few squares east so it is chargeable
    dx = 8 - enemy_unit.x
    dy = 3 - enemy_unit.y
    enemy_unit.x += dx
    enemy_unit.y += dy
    for m in enemy_unit.models:
        m.x += dx
        m.y += dy
    board.place_unit(enemy_unit)

    called = {}

    def mock_move_unit(unit, x, y):
        called["args"] = (unit, x, y)
        return True

    monkeypatch.setattr(board, "move_unit", mock_move_unit)
    monkeypatch.setattr(charge_phase.random, "randint", lambda a, b: 6)

    responses = iter(["y", "1", "y"])

    def get_input(_):
        return next(responses)

    charge_phase.charge_phase(board, [player_unit], get_input, lambda *_: None)

    assert called.get("args") is not None
    assert len(called["args"]) == 3
    assert called["args"][0] is player_unit

