from flask import Flask, render_template, request
from game_phases.deployment import get_deployment_zones
import random

app = Flask(__name__)

BOARD_WIDTH = 60
BOARD_HEIGHT = 44

# Global state variables
player_faction = None
roll_result = None
selected_realm = None
objectives = []
deployment_map = None
defender_zone_func = None
attacker_zone_func = None

@app.route("/", methods=["GET", "POST"])
def index():
    global player_faction, roll_result, selected_realm, objectives
    global deployment_map, defender_zone_func, attacker_zone_func

    if request.method == "POST":
        action = request.form.get("action")

        if action == "select_faction":
            player_faction = request.form.get("faction")

        elif action == "roll_off":
            player_roll = random.randint(1, 6)
            ai_roll = random.randint(1, 6)
            if player_roll > ai_roll:
                roll_result = f"You won the roll-off! (You: {player_roll}, AI: {ai_roll})"
            elif ai_roll > player_roll:
                roll_result = f"AI won the roll-off. (You: {player_roll}, AI: {ai_roll})"
            else:
                roll_result = f"It's a tie! (You: {player_roll}, AI: {ai_roll}) Roll again."

        elif action == "select_realm":
            selected_realm = request.form.get("realm")
            if selected_realm == "Aqshy":
                objectives = [(7, 7), (51, 7), (30, 22), (10, 38), (53, 38)]
            elif selected_realm == "Ghyran":
                objectives = [(1, 22), (30, 22), (58, 22), (15, 7), (45, 37)]

        elif action == "select_deployment_map":
            deployment_map = request.form.get("map")
            defender_zone_func, attacker_zone_func = get_deployment_zones(board=None, map_type=deployment_map)

    # Calculate objective highlight radius (3" = 6 grid units)
    highlighted = set()
    for ox, oy in objectives:
        for dx in range(-6, 7):
            for dy in range(-6, 7):
                x, y = ox + dx, oy + dy
                if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
                    if dx**2 + dy**2 <= 36:
                        highlighted.add((x, y))

    # Get deployment zones
    team1_zone = set()
    team2_zone = set()

    if defender_zone_func and attacker_zone_func:
        for x in range(BOARD_WIDTH):
            for y in range(BOARD_HEIGHT):
                if defender_zone_func(x, y):
                    team1_zone.add((x, y))
                elif attacker_zone_func(x, y):
                    team2_zone.add((x, y))

    print("DEBUG STATE:")
    print(f"player_faction = {player_faction}")
    print(f"roll_result = {roll_result}")
    print(f"selected_realm = {selected_realm}")
    print(f"deployment_map = {deployment_map}")


    return render_template(
        "index.html",
        width=BOARD_WIDTH,
        height=BOARD_HEIGHT,
        player_faction=player_faction,
        roll_result=roll_result,
        selected_realm=selected_realm,
        deployment_map=deployment_map,
        objectives=objectives,
        highlighted=highlighted,
        team1_zone=team1_zone,
        team2_zone=team2_zone
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
