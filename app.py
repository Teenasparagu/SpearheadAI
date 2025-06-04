from flask import Flask, render_template, request, redirect, session
from game_logic.board import Board
from game_logic.game_state import GameState
from game_logic.game_engine import GameEngine, run_deployment_phase
from game_phases.deployment import get_deployment_zones
import math

app = Flask(__name__)
app.secret_key = "supersecret"  # Required for Flask session

# Initialize game
game = GameEngine()
game_state = game.game_state
board = game.board

# Shared prompt state
input_sequence = []
input_index = 0

@app.route("/game", methods=["GET", "POST"])
def game_view():
    global input_index

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

            def get_input(prompt):
                return inputs.get(prompt, "")

            # Run deployment using stored inputs
            run_deployment_phase(game_state, board, get_input, game_state.log_message)

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

    return render_template(
        "game.html",
        grid=display_grid,
        width=board.width,
        height=board.height,
        prompt_label=prompt_label,
        messages=game_state.messages
    )

@app.route("/reset")
def reset_game():
    session.clear()
    game.__init__()  # Re-initialize the game engine
    return redirect("/game")

if __name__ == "__main__":
    app.run(debug=True)
