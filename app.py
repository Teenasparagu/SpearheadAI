try:
    from flask import Flask, render_template, request, redirect, session
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Flask is required to run the web interface. Install dependencies via 'pip install -r requirements.txt'."
    ) from exc
import base64
import pickle
import random
import math
from game_logic.game_engine import GameEngine
from game_phases import deployment
from game_phases.deployment import (
    get_deployment_zones,
    formation_offsets,
)

from game_phases.movement_phase import move_unit_to
from game_phases import shooting_phase, charge_phase, combat_phase, victory_phase
from game_logic.units import is_in_combat, Model


def _triangle_offsets(num, orientation):
    """Wrapper using deployment's triangle formation."""
    return formation_offsets("triangle", num, orientation)


def _rectangle_offsets(num, orientation):
    return formation_offsets("box", num, orientation)


def _circle_offsets(num, orientation):
    return formation_offsets("circle", num, orientation)

app = Flask(__name__)
app.secret_key = "supersecret"  # Required for Flask session


def _load_game() -> GameEngine:
    """Load the GameEngine instance from the session or create a new one."""
    if "game_data" not in session:
        game = GameEngine()
        session["game_data"] = base64.b64encode(pickle.dumps(game)).decode("utf-8")
        return game
    return pickle.loads(base64.b64decode(session["game_data"]))


def _save_game(game: GameEngine) -> None:
    """Persist the GameEngine instance back into the session."""
    session["game_data"] = base64.b64encode(pickle.dumps(game)).decode("utf-8")


def build_display_grid(game_state, board, preview=None):
    grid_data = game_state.to_grid_dict()
    display_grid = {}
    map_type = game_state.map_layout or "straight"
    defender_zone, attacker_zone = get_deployment_zones(board, map_type)

    for y in range(board.height):
        for x in range(board.width):
            tile = grid_data[(x, y)]
            color = "white"
            label = ""

            if defender_zone(x, y):
                color = "#d0e6ff"
            if attacker_zone(x, y):
                color = "#ffd0d0"
            for obj in board.objectives:
                if math.hypot(x - obj.x, y - obj.y) <= 6:
                    if obj.control_team == 1:
                        color = "#a0c4ff"
                        label = "O"
                    elif obj.control_team == 2:
                        color = "#ffb3b3"
                        label = "O"
                    else:
                        color = "#d9d9d9"
                        label = "O"
            if tile["terrain"]:
                color = "black"
                label = "T"
            if tile["leader1"]:
                color = "#0044cc"
                label = "L"
            elif tile["team1"]:
                color = "#3399ff"
                label = "U"
            elif tile["leader2"]:
                color = "#cc0000"
                label = "L"
            elif tile["team2"]:
                color = "#ff6666"
                label = "U"

            display_grid[(x, y)] = {"color": color, "label": label}

    if preview:
        for px, py in preview:
            if 0 <= px < board.width and 0 <= py < board.height:
                display_grid[(px, py)] = {"color": "#888888", "label": "T"}

    return display_grid

# Shared prompt state
input_sequence = []
input_index = 0


@app.route("/")
def index():
    """Redirect the root URL to the game view."""
    return redirect("/game")





@app.route("/game", methods=["GET", "POST"])
def game_view():
    global input_index
    game = _load_game()
    game_state = game.game_state
    board = game.board

    # Step 1: On first visit, setup the input sequence
    if "initialized" not in session:
        session["initialized"] = True
        session["inputs"] = {}  # Store user inputs
        input_index = 0
        input_sequence.clear()
        factions = deployment.list_factions()
        input_sequence.extend([
            {
                "prompt": "Enter number:",
                "type": "faction",
                "label": "Choose your faction",
                "choices": [{"value": str(i + 1), "label": f.title()} for i, f in enumerate(factions)],
            },
            {
                "prompt": "Choose attacker or defender (a/d):",
                "type": "attacker",
                "label": "Choose attacker or defender",
                "choices": [{"value": "a", "label": "Attacker"}, {"value": "d", "label": "Defender"}],
            },
            {
                "prompt": "(a/g):",
                "type": "realm",
                "label": "Choose a realm",
                "choices": [{"value": "a", "label": "Aqshy"}, {"value": "g", "label": "Ghyran"}],
            },
            {
                "prompt": "Enter 1 or 2:",
                "type": "map",
                "label": "Choose deployment map",
                "choices": [{"value": "1", "label": "Straight"}, {"value": "2", "label": "Diagonal"}],
            },
            {
                "prompt": "Do you want to go first or second?:",
                "type": "first_turn",
                "label": "First turn choice",
                "choices": [{"value": "first", "label": "First"}, {"value": "second", "label": "Second"}],
            },
        ])

    # Step 2: Handle submitted input
    if request.method == "POST":
        user_input = request.form.get("input")
        prompt_key = input_sequence[input_index]["prompt"]
        session["inputs"][prompt_key] = user_input
        input_index += 1

        if input_index >= len(input_sequence):
            game_state.phase = "hero"
            _save_game(game)
            return redirect("/hero")

    # Step 3: Get next prompt
    if input_index >= len(input_sequence):
        return redirect("/hero")


    current = input_sequence[input_index]
    prompt_label = current["label"]
    choices = current.get("choices")

    display_grid = build_display_grid(game_state, board)

    response = render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label=prompt_label,
        choices=choices,
        messages=game_state.messages
    )
    _save_game(game)
    return response

@app.route("/reset")
def reset_game():
    session.clear()
    session.pop("game_data", None)
    global input_index
    input_index = 0
    return redirect("/game")


@app.route("/grid")
def display_grid():
    """Display the current game board after setup."""
    game = _load_game()
    game_state = game.game_state
    board = game.board
    display_grid = build_display_grid(game_state, board)

    response = render_template(
        "grid.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        messages=game_state.messages,
    )
    _save_game(game)
    return response


@app.route("/hero", methods=["GET", "POST"])
def hero_phase_view():
    game = _load_game()
    game_state = game.game_state
    board = game.board

    if request.method == "POST":
        game_state.phase = "movement"
        _save_game(game)
        return redirect("/move")

    display_grid = build_display_grid(game_state, board)
    response = render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label="Hero Phase",
        choices=[{"value": "next", "label": "Next Phase"}],
        messages=game_state.messages,
    )
    _save_game(game)
    return response




@app.route("/move", methods=["GET", "POST"])
def move_unit_view():
    game = _load_game()
    game_state = game.game_state
    board = game.board
    state = session.get("move_state", {"step": "select"})
    player_units = game_state.units.get("player", [])

    if request.method == "POST":
        if "finish" in request.form:
            session.pop("move_state", None)
            game_state.phase = "shooting"
            _save_game(game)
            return redirect("/shoot")

        step = state.get("step")
        if step == "select" and "pos" in request.form:
            x_str, y_str = request.form.get("pos").split(",")
            x, y = int(x_str), int(y_str)
            for idx, u in enumerate(player_units):
                if any(m.x == x and m.y == y for m in u.models):
                    state["unit_idx"] = idx
                    unit = u
                    if is_in_combat(unit.models[0].x, unit.models[0].y, board, unit.team):
                        state["step"] = "combat_choice"
                    else:
                        state["step"] = "move_type"
                    break
            else:
                game_state.log_message("No unit at that position.")

        elif step == "combat_choice" and "action" in request.form:
            unit = player_units[state["unit_idx"]]
            if request.form["action"] == "stay":
                game_state.log_message(f"{unit.name} stays in combat.")
                state = {"step": "select"}
            else:  # retreat
                state["move_range"] = unit.move_range
                unit.has_run = True
                state["step"] = "dest"

        elif step == "move_type" and "action" in request.form:
            unit = player_units[state["unit_idx"]]
            if request.form["action"] == "normal":
                state["move_range"] = unit.move_range
                unit.has_run = False
                state["step"] = "dest"
            elif request.form["action"] == "run":
                run_bonus = random.randint(1, 6)
                state["move_range"] = unit.move_range + run_bonus * 2
                unit.has_run = True
                game_state.log_message(f"{unit.name} runs! Rolled {run_bonus}.")
                state["step"] = "dest"

        elif step == "dest" and "pos" in request.form:
            unit = player_units[state["unit_idx"]]
            x_str, y_str = request.form.get("pos").split(",")
            x, y = int(x_str), int(y_str)
            moved = move_unit_to(unit, board, x, y, state.get("move_range", unit.move_range), game_state.log_message)
            if moved:
                state = {"step": "select"}
            else:
                game_state.log_message("Invalid destination.")

        elif "cancel" in request.form:
            state = {"step": "select"}

    session["move_state"] = state
    step = state.get("step")
    if step == "select":
        prompt_label = "Select a unit (click on the grid) or Finish"
    elif step == "combat_choice":
        prompt_label = "Unit in combat: Stay or Retreat?"
    elif step == "move_type":
        prompt_label = "Choose Move or Run"
    else:  # dest
        prompt_label = "Select destination"

    display_grid = build_display_grid(game_state, board)
    response = render_template(
        "movement.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label=prompt_label,
        step=step,
        messages=game_state.messages,
    )
    _save_game(game)
    return response


@app.route("/shoot", methods=["GET", "POST"])
def shooting_phase_view():
    game = _load_game()
    game_state = game.game_state
    board = game.board

    if request.method == "POST":
        shooting_phase.player_shooting_phase(
            board,
            game_state.units.get("player", []),
            game_state.units.get("ai", []),
            lambda _: "0",
            game_state.log_message,
        )
        game_state.phase = "charge"
        _save_game(game)
        return redirect("/charge")

    display_grid = build_display_grid(game_state, board)
    response = render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label="Shooting Phase",
        choices=[{"value": "next", "label": "Resolve"}],
        messages=game_state.messages,
    )
    _save_game(game)
    return response


@app.route("/charge", methods=["GET", "POST"])
def charge_phase_view():
    game = _load_game()
    game_state = game.game_state
    board = game.board

    if request.method == "POST":
        charge_phase.charge_phase(
            board,
            game_state.units.get("player", []),
            lambda _: "n",
            game_state.log_message,
        )
        game_state.phase = "combat"
        _save_game(game)
        return redirect("/combat")

    display_grid = build_display_grid(game_state, board)
    response = render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label="Charge Phase",
        choices=[{"value": "next", "label": "Resolve"}],
        messages=game_state.messages,
    )
    _save_game(game)
    return response


@app.route("/combat", methods=["GET", "POST"])
def combat_phase_view():
    game = _load_game()
    game_state = game.game_state
    board = game.board

    if request.method == "POST":
        combat_phase.combat_phase(
            board,
            current_team=1,
            player_units=game_state.units.get("player", []),
            ai_units=game_state.units.get("ai", []),
            get_input=lambda _: "",
            log=game_state.log_message,
        )
        game_state.phase = "end"
        _save_game(game)
        return redirect("/end")

    display_grid = build_display_grid(game_state, board)
    response = render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label="Combat Phase",
        choices=[{"value": "next", "label": "Resolve"}],
        messages=game_state.messages,
    )
    _save_game(game)
    return response


@app.route("/end", methods=["GET", "POST"])
def end_phase_view():
    game = _load_game()
    game_state = game.game_state
    board = game.board

    if request.method == "POST":
        victory_phase.process_end_phase_actions(
            board,
            game_state.units.get("player", []),
            lambda _: "",
            game_state.log_message,
        )
        game_state.phase = "victory"
        _save_game(game)
        return redirect("/victory")

    display_grid = build_display_grid(game_state, board)
    response = render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label="End Phase",
        choices=[{"value": "next", "label": "Resolve"}],
        messages=game_state.messages,
    )
    _save_game(game)
    return response


@app.route("/victory", methods=["GET", "POST"])
def victory_phase_view():
    game = _load_game()
    game_state = game.game_state
    board = game.board

    if request.method == "POST":
        board.update_objective_control()
        victory_phase.calculate_victory_points(
            board,
            game_state.total_vp,
            1,
            lambda _: "",
            game_state.log_message,
        )
        game_state.phase = "hero"
        _save_game(game)
        return redirect("/hero")

    display_grid = build_display_grid(game_state, board)
    response = render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label="Victory Phase",
        choices=[{"value": "next", "label": "Resolve"}],
        messages=game_state.messages,
    )
    _save_game(game)
    return response

if __name__ == "__main__":
    app.run(debug=True)
