from flask import Flask, render_template, request, redirect, url_for
from game_logic.game_engine import GameEngine
from threading import Thread
import queue
from game_phases.deployment import get_deployment_zones, formation_offsets
import math

# Shared engine instance used by the CLI runner and this viewer
engine = GameEngine()
input_queue: queue.Queue[str] = queue.Queue()
current_prompt: str = ""
game_thread: Thread | None = None


def _triangle_offsets(num, orientation):
    """Wrapper using deployment's triangle formation."""
    return formation_offsets("triangle", num, orientation)


def _rectangle_offsets(num, orientation):
    return formation_offsets("box", num, orientation)


def _circle_offsets(num, orientation):
    return formation_offsets("circle", num, orientation)

app = Flask(__name__)


def log(msg: str) -> None:
    """Append a message to the game log."""
    engine.game_state.log_message(msg)


def get_input(prompt: str) -> str:
    """Retrieve input from the web client via a queue."""
    global current_prompt
    current_prompt = prompt
    engine.game_state.log_message(prompt)
    return input_queue.get()


def _run_game() -> None:
    """Run the game loop in a background thread."""
    engine.run_game(get_input=get_input, log=log)


def start_game() -> None:
    """Ensure the game thread is running."""
    global game_thread
    if game_thread is None or not game_thread.is_alive():
        game_thread = Thread(target=_run_game, daemon=True)
        game_thread.start()


def build_display_grid(game_state, board):
    """Return a mapping of board coordinates to color/label for display."""
    grid_data = game_state.to_grid_dict()
    display_grid = {}
    defender_zone, attacker_zone = get_deployment_zones(board, game_state.map_layout or "straight")

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


@app.route("/")
def show_board():
    """Render the board in its current state."""
    grid = build_display_grid(engine.game_state, engine.board)
    return render_template(
        "grid.html",
        grid=grid,
        width=engine.board.width,
        height=engine.board.height,
        messages=engine.game_state.messages,
    )


@app.route("/game", methods=["GET", "POST"])
def interactive_game():
    """Interactive view that accepts user commands."""
    start_game()
    if request.method == "POST":
        input_queue.put(request.form["input"])
        return redirect(url_for("interactive_game"))

    grid = build_display_grid(engine.game_state, engine.board)
    return render_template(
        "game.html",
        grid=grid,
        width=engine.board.width,
        height=engine.board.height,
        prompt_label=current_prompt,
        choices=None,
        messages=engine.game_state.messages,
    )


@app.route("/reset")
def reset_game():
    """Reset the game state and restart the thread."""
    global engine, input_queue, current_prompt
    engine = GameEngine()
    input_queue = queue.Queue()
    current_prompt = ""
    start_game()
    return redirect(url_for("interactive_game"))



if __name__ == "__main__":
    start_game()
    app.run(debug=True)

