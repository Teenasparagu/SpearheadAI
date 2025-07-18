from flask import Flask, render_template
from game_logic.game_engine import GameEngine
from game_phases.deployment import get_deployment_zones, formation_offsets
import math

# Shared engine instance used by the CLI runner and this viewer
engine = GameEngine()


def _triangle_offsets(num, orientation, base_width=1.0, base_height=1.0):
    """Wrapper using deployment's triangle formation."""
    return formation_offsets("triangle", num, orientation, base_width, base_height)


def _rectangle_offsets(num, orientation, base_width=1.0, base_height=1.0):
    return formation_offsets("box", num, orientation, base_width, base_height)


def _circle_offsets(num, orientation, base_width=1.0, base_height=1.0):
    return formation_offsets("circle", num, orientation, base_width, base_height)

app = Flask(__name__)


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
                label = "L" if tile["center"] else "l"
            elif tile["team1"]:
                color = "#3399ff"
                label = "U" if tile["center"] else "u"
            elif tile["leader2"]:
                color = "#cc0000"
                label = "L" if tile["center"] else "l"
            elif tile["team2"]:
                color = "#ff6666"
                label = "U" if tile["center"] else "u"

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



if __name__ == "__main__":
    app.run(debug=True)

