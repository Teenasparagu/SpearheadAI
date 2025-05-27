from game_logic.units import Unit

# game_logic/factions/stormcast.py
unit_definitions = {
    "Liberators": {
        "move_range": 10,
        "control_score": 2,
        "health": 2,
        "num_models" : 5,
        "base_width": 1.5,
        "base_height": 1.5,
    },
    "Prosecutors": {
        "move_range": 24,
        "control_score": 1,
        "health": 2,
        "num_models" : 3,
        "base_width": 1.5,
        "base_height": 1.5,
    },
    "Lord-Veritant": {
        "move_range": 5,
        "control_score": 2,
        "health": 6,
        "num_models": 1,
        "base_width": 1.5,   # in inches
        "base_height": 1.5   # use 2.0 or 2.5 for cavalry/mounted units
    },
    "Lord-Vigilant": {
        "move_range": 12,
        "control_score": 2,
        "health": 8,
        "num_models": 1,
        "base_width": 2.0,   # in inches
        "base_height": 3.5   # use 2.0 or 2.5 for cavalry/mounted units
    },
    # Add other units here...
}

def create_force(team=1):
    return [
        Unit(name="Lord-Vigilant", faction="stormcast", team=team, num_models=1),
        Unit(name="Prosecutors", faction="stormcast", team=team, num_models=3),
        Unit(name="Liberators", faction="stormcast", team=team, num_models=5),
        Unit(name="Lord-Veritant", faction="stormcast", team=team, num_models=1)
    ]