from game_logic.units import Unit

unit_definitions = {
    "Clanrats": {
        "move_range": 12,
        "control_score": 1,
        "health": 1,  
        "num_models" : 10,
        "base_diameter": 1,
    },
    
    "Rat Ogors": {
        "move_range": 12,
        "control_score": 1,
        "health": 4,
        "num_models": 3,
        "base_diameter": 2,
    }
}

def create_force(team=2):
    return [
        Unit(name="Rat Ogors", x=7, y=7, faction="skaven", team=team, num_models=3),
        Unit(name="Clanrats", x=15, y=15, faction="skaven", team=team, num_models=10),
    ]


