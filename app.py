from flask import Flask, render_template, request, redirect, session
import base64
import pickle
import random
import math
from game_logic.game_engine import GameEngine
from game_phases import deployment
from game_phases.deployment import get_deployment_zones
from game_phases.movement_phase import player_unit_move, attempt_move
from game_logic.units import is_in_combat
from game_logic.utils import _simple_deploy_units, within_enemy_buffer, valid_model_position

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


def build_display_grid(game_state, board):
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
        _simple_deploy_units(board, player_units, defender_zone, zone_name, "Player")
        _simple_deploy_units(board, ai_units, attacker_zone, zone_name, "AI")
    else:
        ai_units = deployment.load_faction_force(ai_faction, team_number=1)
        player_units = deployment.load_faction_force(player_faction, team_number=2)
        _simple_deploy_units(board, ai_units, defender_zone, zone_name, "AI")
        _simple_deploy_units(board, player_units, attacker_zone, zone_name, "Player")

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


def apply_partial_deployment(game_state, board, inputs, final=False, manual=False):
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

        if defender == "player":
            player_units = deployment.load_faction_force(player_faction, team_number=1)
            ai_units = deployment.load_faction_force(ai_faction, team_number=2)
            if manual:
                _simple_deploy_units(board, ai_units, attacker_zone, zone_name, "AI")
            else:
                _simple_deploy_units(board, player_units, defender_zone, zone_name, "Player")
                _simple_deploy_units(board, ai_units, attacker_zone, zone_name, "AI")
        else:
            ai_units = deployment.load_faction_force(ai_faction, team_number=1)
            player_units = deployment.load_faction_force(player_faction, team_number=2)
            if manual:
                _simple_deploy_units(board, ai_units, defender_zone, zone_name, "AI")
            else:
                _simple_deploy_units(board, ai_units, defender_zone, zone_name, "AI")
                _simple_deploy_units(board, player_units, attacker_zone, zone_name, "Player")

        if manual:
            game_state.units["ai"] = ai_units
            game_state.units["player"] = []
            game_state.pending_units = player_units
            game_state.player_zone = {(x, y) for x in range(board.width) for y in range(board.height) if (defender_zone if defender == "player" else attacker_zone)(x, y)}
            game_state.enemy_zone = {(x, y) for x in range(board.width) for y in range(board.height) if (attacker_zone if defender == "player" else defender_zone)(x, y)}
            if attacker == "player":
                first_choice = inputs.get("Do you want to go first or second?:", "first").strip().lower()
                game_state.pending_first = "player" if first_choice.startswith("first") else "ai"
            else:
                game_state.pending_first = "ai"
                game_state.log_message("AI chooses ai to go first.")
            game_state.phase = "deployment"
            game_state.log_message("Place your units on the board.")
        else:
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

        if input_index >= len(input_sequence):
            inputs = session["inputs"]
            apply_partial_deployment(game_state, board, inputs, final=True, manual=True)
            _save_game(game)
            return redirect("/deploy")

    # Step 3: Get next prompt
    if input_index >= len(input_sequence):
        return redirect("/deploy")

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
        prompt_label=None,
        clickable=False,
        click_url="/deploy"
    )
    _save_game(game)
    return response


@app.route("/deploy", methods=["GET", "POST"])
def deploy_view():
    game = _load_game()
    gs = game.game_state
    board = game.board

    if gs.phase != "deployment" or not gs.pending_units:
        return redirect("/grid")

    state = session.get("deploy_state", {"unit_idx": 0, "stage": "select"})
    units = gs.pending_units

    if state["unit_idx"] >= len(units):
        gs.units["player"] = units
        gs.phase = "hero"
        first = gs.pending_first or "player"
        gs.turn_order = [first, "ai" if first == "player" else "player"]
        gs.log_message("Deployment phase complete.")
        session.pop("deploy_state", None)
        _save_game(game)
        return redirect("/grid")

    unit = units[state["unit_idx"]]

    if request.method == "POST" and state.get("stage") in {"confirm", "confirm_individual"}:
        action = request.form.get("action")
        if action == "confirm":
            state["unit_idx"] += 1
            state["stage"] = "select"
            for k in ("prev", "model_idx", "placed"):
                state.pop(k, None)
        elif action in {"redo", "restart"}:
            board.remove_unit(unit)
            prev = state.get("prev")
            if prev:
                for m, (ox, oy) in zip(unit.models, prev):
                    m.x, m.y = ox, oy
            state["stage"] = "select"
            for k in ("prev", "model_idx", "placed"):
                state.pop(k, None)
        elif action == "individual" and state.get("stage") == "confirm":
            board.remove_unit(unit)
            prev = state.get("prev")
            if prev:
                for m, (ox, oy) in zip(unit.models, prev):
                    m.x, m.y = ox, oy
            state["stage"] = "model"
            state["model_idx"] = 0
            state["placed"] = []

    elif request.method == "GET" and "x" in request.args and "y" in request.args and state.get("stage") == "select":
        x = int(request.args.get("x"))
        y = int(request.args.get("y"))
        if (x, y) not in gs.player_zone:
            gs.log_message("❌ Not within your deployment zone.")
        else:
            dx = x - unit.models[0].x
            dy = y - unit.models[0].y
            too_close = False
            for m in unit.models:
                nx, ny = m.x + dx, m.y + dy
                if within_enemy_buffer(nx, ny, gs.enemy_zone):
                    too_close = True
                    break
            if too_close:
                gs.log_message("❌ Cannot deploy within 6\" of enemy territory.")
            else:
                prev = [(m.x, m.y) for m in unit.models]
                for m in unit.models:
                    m.x += dx
                    m.y += dy
                if board.place_unit(unit):
                    state["stage"] = "confirm"
                    state["prev"] = prev
                else:
                    for m, (ox, oy) in zip(unit.models, prev):
                        m.x, m.y = ox, oy
                    gs.log_message("❌ Invalid placement.")

    elif request.method == "GET" and "x" in request.args and "y" in request.args and state.get("stage") == "model":
        idx = state.get("model_idx", 0)
        x = int(request.args.get("x"))
        y = int(request.args.get("y"))
        model = unit.models[idx]
        ox, oy = model.x, model.y
        model.x, model.y = x, y
        placed = unit.models[:idx]
        if valid_model_position(model, board, gs.enemy_zone, placed) and all(valid_model_position(m, board, gs.enemy_zone, placed[:i]) for i, m in enumerate(placed)):
            idx += 1
            state["model_idx"] = idx
            if idx >= len(unit.models):
                if board.place_unit(unit):
                    state["stage"] = "confirm_individual"
                else:
                    gs.log_message("❌ Invalid placement.")
                    for m, (px, py) in zip(unit.models, state["prev"]):
                        m.x, m.y = px, py
                    state["stage"] = "select"
                    board.remove_unit(unit)
        else:
            model.x, model.y = ox, oy
            gs.log_message("❌ Invalid placement.")

    session["deploy_state"] = state
    stage = state.get("stage")
    if stage == "select":
        prompt_label = f"Place {unit.name} (click board)"
    elif stage == "model":
        prompt_label = f"Place model {state.get('model_idx',0)+1} of {unit.name}"
    else:
        prompt_label = f"Confirm {unit.name}?"
    display_grid = build_display_grid(gs, board)
    response = render_template(
        "grid.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        messages=gs.messages,
        prompt_label=prompt_label,
        clickable=stage in {"select", "model"},
        click_url="/deploy",
    )
    if stage == "confirm":
        response = response.replace(
            "</body>",
            "<form method='POST' style='text-align:center;'><button name='action' value='confirm'>Confirm</button> <button name='action' value='redo'>Reposition</button> <button name='action' value='individual'>Adjust Models</button></form></body>"
        )
    elif stage == "confirm_individual":
        response = response.replace(
            "</body>",
            "<form method='POST' style='text-align:center;'><button name='action' value='confirm'>Confirm</button> <button name='action' value='restart'>Restart</button></form></body>"
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
        user_input = request.form.get("input", "").strip().lower()
        step = state.get("step")

        if step == "select":
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(player_units):
                    state["unit_idx"] = idx
                    unit = player_units[idx]
                    if is_in_combat(unit.models[0].x, unit.models[0].y, board, unit.team):
                        game_state.log_message(f"{unit.name} is in combat.")
                        state["step"] = "retreat_choice"
                    else:
                        state["step"] = "move_choice"
                else:
                    game_state.log_message("Invalid unit selection.")
            except ValueError:
                game_state.log_message("Invalid input.")

        elif step == "retreat_choice":
            unit = player_units[state["unit_idx"]]
            if user_input.startswith("y"):
                state["step"] = "retreat_dir"
            else:
                game_state.log_message(f"{unit.name} ends its movement without retreating.")
                session.pop("move_state", None)
                _save_game(game)
                return redirect("/grid")

        elif step == "retreat_dir":
            unit = player_units[state["unit_idx"]]
            if user_input == "skip":
                game_state.log_message(f"{unit.name} skipped their retreat.")
                session.pop("move_state", None)
            else:
                if attempt_move(unit, board, user_input, unit.move_range, game_state.log_message):
                    dmg = random.randint(1, 3)
                    game_state.log_message(f"{unit.name} suffers {dmg} damage while retreating!")
                    unit.apply_damage(dmg)
                    session.pop("move_state", None)
                else:
                    game_state.log_message("Invalid move.")

        elif step == "move_choice":
            unit = player_units[state["unit_idx"]]
            if user_input.startswith("n"):
                game_state.log_message(f"{unit.name} does not move.")
                session.pop("move_state", None)
            elif user_input.startswith("r"):
                run_bonus = random.randint(1, 6)
                state["move_range"] = unit.move_range + run_bonus * 2
                unit.has_run = True
                game_state.log_message(f"{unit.name} runs! Rolled {run_bonus}.")
                state["step"] = "direction"
            elif user_input.startswith("m"):
                state["move_range"] = unit.move_range
                unit.has_run = False
                state["step"] = "direction"
            else:
                game_state.log_message("Invalid option.")

        elif step == "direction":
            unit = player_units[state["unit_idx"]]
            if user_input == "skip":
                game_state.log_message(f"{unit.name} skipped their move.")
                session.pop("move_state", None)
            else:
                if attempt_move(unit, board, user_input, state.get("move_range", unit.move_range), game_state.log_message):
                    session.pop("move_state", None)
                else:
                    game_state.log_message("Invalid move.")

    step = session.get("move_state", state).get("step")
    if step == "select":
        prompt_label = "Select a unit to move (number)"
    elif step == "retreat_choice":
        prompt_label = "Retreat? (y/n)"
    elif step == "retreat_dir":
        prompt_label = "Enter retreat direction and distance or 'skip'"
    elif step == "move_choice":
        prompt_label = "Choose movement - N = No Move, M = Move, R = Run"
    else:  # direction
        prompt_label = "Enter direction and distance or 'skip'"

    session["move_state"] = state
    display_grid = build_display_grid(game_state, board)
    response = render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label=prompt_label,
        messages=game_state.messages,
    )
    _save_game(game)
    return response

if __name__ == "__main__":
    app.run(debug=True)
