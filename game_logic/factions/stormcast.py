from game_logic.units import Unit

# game_logic/factions/stormcast.py
unit_definitions = {
    "Liberators": {
        "move_range": 10,
        "control_score": 2,
        "health": 2,
        "num_models" : 5,
        "base_diameter": 1.5,
    },
    "Prosecutors": {
        "move_range": 24,
        "control_score": 1,
        "health": 2,
        "num_models" : 3,
        "base_diameter": 1.5,
    },
    # Add other units here...
}

def create_force(team=1):
    return [
        Unit(name="Prosecutors", x=2, y=2, faction="stormcast", team=team, num_models=3),
        Unit(name="Liberators", x=10, y=10, faction="stormcast", team=team, num_models=5),
    ]