from game_logic.units import Unit

unit_definitions = {
    "Clanrats": {
        "move_range": 12,
        "control_score": 1,
        "health": 1,  
        "num_models": 10,
        "base_width": 1.0,    # circular base: 1" diameter
        "base_height": 1.0,
    },
    
    "Rat Ogors": {
        "move_range": 12,
        "control_score": 1,
        "health": 4,
        "num_models": 3,
        "base_width": 2,    # oval base: 2.5" long
        "base_height": 2,   # and 1.5" wide
    },

    "Clawlord": {
        "move_range": 9,
        "control_score": 2,
        "health": 7,
        "num_models": 1,
        "base_width": 2,
        "base_height": 3,
    },

        "Grey Seer": {
        "move_range": 6,
        "control_score": 2,
        "health": 5,
        "num_models": 1,
        "base_width": 1.5,
        "base_height": 1.5,
    },

    "Warlock Engineer": {
        "move_range": 6,
        "control_score": 2,
        "health": 5,
        "num_models": 2,
        "base_width": 1.5,
        "base_height": 1.5,
    },
}

def create_force(team=2):
    return [
        Unit(name="Clawlord", faction="skaven", team=team, num_models=1),
        Unit(name="Grey Seer", faction="skaven", team=team, num_models=1),
        Unit(name="Warlock Engineer", faction="skaven", team=team, num_models=1),   
        Unit(name="Rat Ogors", faction="skaven", team=team, num_models=3),
        Unit(name="Clanrats", faction="skaven", team=team, num_models=10),
        Unit(name="Clanrats", faction="skaven", team=team, num_models=10), 
    ]