from flask import Flask, render_template, request, redirect, session
import base64
import pickle
from game_logic.game_engine import GameEngine
from game_phases import deployment
from game_phases.deployment import get_deployment_zones
from game_logic.utils import _simple_deploy_units
import math

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
        input_sequence.extend([
            {"prompt": "Enter number:", "type": "faction", "label": "Choose your faction"},
            {"prompt": "Choose attacker or defender (a/d):", "type": "attacker", "label": "Choose attacker or defender"},
            {"prompt": "(a/g):", "type": "realm", "label": "Choose a realm (a = Aqshy, g = Ghyran)"},
            {"prompt": "Enter 1 or 2:", "type": "map", "label": "Choose deployment map (1 = straight, 2 = diagonal)"},
            {"prompt": "Do you want to go first or second?:", "type": "first_turn", "label": "First turn choice"}
        ])

    # Step 2: Handle submitted input
    if request.method == "POST":
        user_input = request.form.get("input")
        prompt_key = input_sequence[input_index]["prompt"]
        session["inputs"][prompt_key] = user_input
        input_index += 1

        if input_index >= len(input_sequence):
            # All inputs received — run deployment
            inputs = session["inputs"]

            # Run a simplified deployment using stored inputs
            run_web_deployment_phase(game_state, board, inputs)
            _save_game(game)

            return redirect("/grid")

    # Step 3: Get next prompt
    current = input_sequence[input_index]
    prompt_label = current["label"]

    # Build visual grid with priorities
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

    response = render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label=prompt_label,
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

    response = render_template(
        "grid.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        messages=game_state.messages,
    )
    _save_game(game)
    return response

if __name__ == "__main__":
    app.run(debug=True)
