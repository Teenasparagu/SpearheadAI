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
    deploy_terrain,
    is_within_zone,
    is_clear_of_objectives,
    is_valid_leader_position,
    formation_offsets,
)
from game_logic.terrain import RECTANGLE_WALL, L_SHAPE_WALL, rotate_shape
from game_phases.movement_phase import move_unit_to
from game_phases import shooting_phase, charge_phase, combat_phase, victory_phase
from game_logic.units import is_in_combat, Model
from game_logic.utils import _simple_deploy_units


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



def run_web_deployment_phase(game_state, board, inputs):
    """Run a trimmed deployment phase using values collected from the web UI."""
    factions = deployment.list_factions()
    choice = int(inputs.get("Enter number:", "1"))
    player_faction = factions[max(0, choice - 1)]
    ai_faction = [f for f in factions if f != player_faction][0]
    game_state.log_message(f"You chose: {player_faction.title()}")
    game_state.log_message(f"AI will play: {ai_faction.title()}")

    role = inputs.get("Choose attacker or defender (a/d):", "a").strip().lower()
    attacker = "player" if role == "a" else "ai"
    defender = "ai" if attacker == "player" else "player"
    game_state.log_message(f"{attacker.capitalize()} is the attacker, {defender} is the defender.")

    realm_choice = inputs.get("(a/g):", "a").strip().lower()
    battlefield = "ghyran" if realm_choice == "g" else "aqshy"
    game_state.realm = battlefield
    board.objectives = deployment.get_objectives_for_battlefield(battlefield)
    game_state.objectives = board.objectives
    game_state.log_message(f"Objectives placed for {battlefield.title()}:")
    for obj in board.objectives:
        game_state.log_message(f" - ({obj.x}, {obj.y})")

    map_choice = inputs.get("Enter 1 or 2:", "1").strip()
    deployment_map = "diagonal" if map_choice == "2" else "straight"
    game_state.map_layout = deployment_map
    zone_name = deployment_map
    defender_zone, attacker_zone = deployment.get_deployment_zones(board, deployment_map)

    if defender == "player":
        player_units = deployment.load_faction_force(player_faction, team_number=1)
        ai_units = deployment.load_faction_force(ai_faction, team_number=2)
        _simple_deploy_units(board, player_units, defender_zone, attacker_zone, zone_name, "Player")
        _simple_deploy_units(board, ai_units, attacker_zone, defender_zone, zone_name, "AI")
    else:
        ai_units = deployment.load_faction_force(ai_faction, team_number=1)
        player_units = deployment.load_faction_force(player_faction, team_number=2)
        _simple_deploy_units(board, ai_units, defender_zone, attacker_zone, zone_name, "AI")
        _simple_deploy_units(board, player_units, attacker_zone, defender_zone, zone_name, "Player")

    game_state.players["attacker"] = attacker
    game_state.players["defender"] = defender
    game_state.units["player"] = player_units
    game_state.units["ai"] = ai_units

    if attacker == "player":
        first_choice = inputs.get("Do you want to go first or second?:", "first").strip().lower()
        first = "player" if first_choice.startswith("first") else "ai"
    else:
        first = "ai"
        game_state.log_message("AI chooses ai to go first.")

    game_state.phase = "hero"
    game_state.turn_order = [first, "ai" if first == "player" else "player"]
    game_state.log_message(f"{first.capitalize()} will take the first turn.")
    game_state.log_message("Deployment phase complete.")


def apply_partial_deployment(game_state, board, inputs, final=False):
    """Update game state based on partially collected deployment inputs."""
    factions = deployment.list_factions()

    if "Enter number:" in inputs and not hasattr(game_state, "player_faction"):
        choice = int(inputs["Enter number:"])
        game_state.player_faction = factions[max(0, choice - 1)]
        game_state.ai_faction = [f for f in factions if f != game_state.player_faction][0]
        game_state.log_message(f"You chose: {game_state.player_faction.title()}")
        game_state.log_message(f"AI will play: {game_state.ai_faction.title()}")

    if "Choose attacker or defender (a/d):" in inputs and not hasattr(game_state, "attacker"):
        role = inputs["Choose attacker or defender (a/d):"].strip().lower()
        attacker = "player" if role == "a" else "ai"
        defender = "ai" if attacker == "player" else "player"
        game_state.attacker = attacker
        game_state.defender = defender
        game_state.players["attacker"] = attacker
        game_state.players["defender"] = defender
        game_state.log_message(f"{attacker.capitalize()} is the attacker, {defender} is the defender.")

    if "(a/g):" in inputs and not board.objectives:
        realm_choice = inputs["(a/g):"].strip().lower()
        battlefield = "ghyran" if realm_choice == "g" else "aqshy"
        game_state.realm = battlefield
        board.objectives = deployment.get_objectives_for_battlefield(battlefield)
        game_state.objectives = board.objectives
        game_state.log_message(f"Objectives placed for {battlefield.title()}:")
        for obj in board.objectives:
            game_state.log_message(f" - ({obj.x}, {obj.y})")

    if "Enter 1 or 2:" in inputs and game_state.map_layout is None:
        map_choice = inputs["Enter 1 or 2:"]
        deployment_map = "diagonal" if map_choice == "2" else "straight"
        game_state.map_layout = deployment_map
        game_state.log_message(f"Deployment map chosen: {deployment_map.title()}")

    if final:
        attacker = game_state.players.get("attacker")
        defender = game_state.players.get("defender")
        player_faction = getattr(game_state, "player_faction", factions[0])
        ai_faction = getattr(game_state, "ai_faction", factions[1])
        deployment_map = game_state.map_layout or "straight"
        zone_name = deployment_map
        defender_zone, attacker_zone = deployment.get_deployment_zones(board, deployment_map)

        if not game_state.units["player"] and not game_state.units["ai"]:
            if defender == "player":
                player_units = deployment.load_faction_force(player_faction, team_number=1)
                ai_units = deployment.load_faction_force(ai_faction, team_number=2)
                _simple_deploy_units(board, player_units, defender_zone, attacker_zone, zone_name, "Player")
                _simple_deploy_units(board, ai_units, attacker_zone, defender_zone, zone_name, "AI")
            else:
                ai_units = deployment.load_faction_force(ai_faction, team_number=1)
                player_units = deployment.load_faction_force(player_faction, team_number=2)
                _simple_deploy_units(board, ai_units, defender_zone, attacker_zone, zone_name, "AI")
                _simple_deploy_units(board, player_units, attacker_zone, defender_zone, zone_name, "Player")
            game_state.units["player"] = player_units
            game_state.units["ai"] = ai_units

        if attacker == "player":
            first_choice = inputs.get("Do you want to go first or second?:", "first").strip().lower()
            first = "player" if first_choice.startswith("first") else "ai"
        else:
            first = "ai"
            game_state.log_message("AI chooses ai to go first.")

        game_state.phase = "hero"
        game_state.turn_order = [first, "ai" if first == "player" else "player"]
        game_state.log_message(f"{first.capitalize()} will take the first turn.")
        game_state.log_message("Deployment phase complete.")


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
        session["terrain_done"] = False
        session["unit_done"] = False
        session["terrain_state"] = {
            "piece_index": 0,
            "pos": None,
            "dir_idx": 0
        }
        session["unit_state"] = {
            "unit_idx": 0,
            "step": "select_pos",
            "pos": None,
            "formation": None,
            "manual": False,
            "model_positions": [],
        }
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
        apply_partial_deployment(game_state, board, session["inputs"])
        input_index += 1

        if prompt_key == "Enter 1 or 2:" and not session.get("terrain_done"):
            _save_game(game)
            return redirect("/terrain")
        if prompt_key == "Do you want to go first or second?:" and not session.get("unit_done"):
            _save_game(game)
            return redirect("/units")

        if input_index >= len(input_sequence):
            inputs = session["inputs"]
            apply_partial_deployment(game_state, board, inputs, final=True)
            _save_game(game)
            return redirect("/hero")

    # Step 3: Get next prompt
    if input_index >= len(input_sequence):
        return redirect("/hero")

    if input_sequence[input_index]["prompt"] == "Do you want to go first or second?:" and not session.get("terrain_done"):
        _save_game(game)
        return redirect("/terrain")
    if input_sequence[input_index]["prompt"] == "Do you want to go first or second?:" and not session.get("unit_done"):
        _save_game(game)
        return redirect("/units")

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


@app.route("/terrain", methods=["GET", "POST"])
def terrain_placement():
    game = _load_game()
    game_state = game.game_state
    board = game.board
    state = session.get("terrain_state", {"piece_index": 0, "pos": None, "dir_idx": 0})

    pieces = [
        ("Rectangle Wall", RECTANGLE_WALL),
        ("L-Shaped Wall", L_SHAPE_WALL),
    ]
    directions = list(rotate_shape.__globals__["DIRECTION_VECTORS"].keys())

    defender_zone, attacker_zone = get_deployment_zones(board, game_state.map_layout or "straight")
    player_zone = defender_zone if game_state.players.get("defender") == "player" else attacker_zone

    if request.method == "POST":
        if "confirm" in request.form:
            if state.get("pos") is not None:
                x, y = state["pos"]
                name, shape = pieces[state["piece_index"]]
                direction = directions[state["dir_idx"] % len(directions)]
                rotated = rotate_shape(shape, direction)
                zone_coords = [(i, j) for i in range(board.width) for j in range(board.height) if player_zone(i, j)]
                enemy_zone_func = attacker_zone if player_zone is defender_zone else defender_zone
                enemy_coords = [(i, j) for i in range(board.width) for j in range(board.height) if enemy_zone_func(i, j)]
                legal, _ = deployment.is_valid_terrain_placement(x, y, rotated, board, zone_coords, enemy_coords)
                if legal and board.place_terrain_piece(x, y, rotated):

                    game_state.log_message(f"Placed {name} at ({x},{y}) facing {direction}")
                    state["piece_index"] += 1
                    state["pos"] = None
                    state["dir_idx"] = 0
                    if state["piece_index"] >= len(pieces):
                        session["terrain_done"] = True
                        # AI placement
                        ai_zone = attacker_zone if player_zone is defender_zone else defender_zone
                        ai_zone_list = [(i, j) for i in range(board.width) for j in range(board.height) if ai_zone(i, j)]
                        player_zone_list = zone_coords
                        deploy_terrain(
                            board,
                            team=2,
                            zone=ai_zone_list,
                            enemy_zone=player_zone_list,
                            get_input=lambda _: "",
                            log=game_state.log_message,
                        )

                        session["terrain_state"] = state
                        _save_game(game)
                        return redirect("/game")
                else:
                    game_state.log_message("Invalid placement.")
        elif "pos" in request.form:
            x_str, y_str = request.form.get("pos").split(",")
            x, y = int(x_str), int(y_str)
            if state.get("pos") == (x, y):
                state["dir_idx"] = (state["dir_idx"] + 1) % len(directions)
            else:
                state["pos"] = (x, y)
                state["dir_idx"] = 0

    session["terrain_state"] = state
    piece_idx = state["piece_index"]
    if piece_idx >= len(pieces):
        session["terrain_done"] = True
        _save_game(game)
        return redirect("/game")

    preview = None
    if state.get("pos") is not None:
        x, y = state["pos"]
        name, shape = pieces[piece_idx]
        direction = directions[state["dir_idx"] % len(directions)]
        rotated = rotate_shape(shape, direction)
        preview = [(x + dx, y + dy) for dx, dy in rotated]
    display_grid = build_display_grid(game_state, board, preview=preview)

    prompt_label = f"Place {pieces[piece_idx][0]} (click to rotate, confirm when done)"

    zone_color = "#d0e6ff" if player_zone is defender_zone else "#ffd0d0"
    zone_name = "Blue" if player_zone is defender_zone else "Red"


    response = render_template(
        "terrain.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label=prompt_label,
        messages=game_state.messages,
        zone_color=zone_color,
        zone_name=zone_name,

    )
    _save_game(game)
    return response


@app.route("/units", methods=["GET", "POST"])
def unit_placement():
    game = _load_game()
    game_state = game.game_state
    board = game.board
    state = session.get(
        "unit_state",
        {
            "unit_idx": 0,
            "positions": [],
        },
    )

    defender_zone, attacker_zone = get_deployment_zones(board, game_state.map_layout or "straight")
    player_zone = defender_zone if game_state.players.get("defender") == "player" else attacker_zone
    enemy_zone = attacker_zone if player_zone is defender_zone else defender_zone

    if not game_state.units["player"]:
        player_faction = getattr(game_state, "player_faction", deployment.list_factions()[0])
        ai_faction = getattr(game_state, "ai_faction", deployment.list_factions()[1])
        if game_state.players.get("defender") == "player":
            player_units = deployment.load_faction_force(player_faction, team_number=1)
            ai_units = deployment.load_faction_force(ai_faction, team_number=2)
        else:
            ai_units = deployment.load_faction_force(ai_faction, team_number=1)
            player_units = deployment.load_faction_force(player_faction, team_number=2)
        game_state.units["player"] = player_units
        game_state.units["ai"] = ai_units

    player_units = game_state.units["player"]
    current_unit = player_units[state["unit_idx"]] if state["unit_idx"] < len(player_units) else None

    if request.method == "POST" and current_unit:
        if "pos" in request.form:
            x_str, y_str = request.form.get("pos").split(",")
            x, y = int(x_str), int(y_str)
            if len(state["positions"]) < len(current_unit.models):
                state["positions"].append((x, y))
        elif "confirm" in request.form:
            if len(state["positions"]) == len(current_unit.models):
                zone_coords = [(i, j) for i in range(board.width) for j in range(board.height) if player_zone(i, j)]
                enemy_coords = [(i, j) for i in range(board.width) for j in range(board.height) if enemy_zone(i, j)]
                for i, (mx, my) in enumerate(state["positions"]):
                    current_unit.models[i].x = mx
                    current_unit.models[i].y = my
                current_unit.x, current_unit.y = state["positions"][0]
                valid, reason = deployment.is_valid_unit_placement(current_unit.x, current_unit.y, current_unit, board, zone_coords, enemy_coords)
                if valid and board.place_unit(current_unit):
                    game_state.log_message(f"Placed {current_unit.name}")
                    state = {"unit_idx": state["unit_idx"] + 1, "positions": []}
                else:
                    game_state.log_message(f"Invalid placement: {reason}")
                    state["positions"] = []

    session["unit_state"] = state
    if state["unit_idx"] >= len(game_state.units["player"]):
        ai_zone = attacker_zone if player_zone is defender_zone else defender_zone
        deployment.deploy_units(board, game_state.units["ai"], ai_zone, player_zone, game_state.map_layout or "straight", "AI", get_input=lambda _: "", log=game_state.log_message)
        session["unit_done"] = True
        _save_game(game)
        return redirect("/game")

    preview = []
    if current_unit:
        for i, (mx, my) in enumerate(state.get("positions", [])):
            preview.extend(
                Model(mx, my, base_diameter=current_unit.models[i].base_diameter).get_occupied_squares()
            )

    display_grid = build_display_grid(game_state, board, preview=preview)

    prompt_label = f"Place {current_unit.name}" if current_unit else "All units placed"

    zone_color = "#d0e6ff" if player_zone is defender_zone else "#ffd0d0"
    zone_name = "Blue" if player_zone is defender_zone else "Red"

    response = render_template(
        "unit_placement.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label=prompt_label,
        messages=game_state.messages,
        zone_color=zone_color,
        zone_name=zone_name,
        models_remaining=len(current_unit.models) - len(state.get("positions", [])) if current_unit else 0,
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
