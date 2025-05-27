from game_logic.units import Unit
from .faction_factory import FactionFactory

class SkavenFactory(FactionFactory):
    faction_name= "skaven"
    unit_definitions = {
        "Clanrats": {
            "count": 2,
            "move_range": 12,
            "control_score": 1,
            "health": 1,  
            "num_models": 10,
            "base_width": 1.0,    # circular base: 1" diameter
            "base_height": 1.0,
            "attacks": []
        },
        
        "Rat Ogors": {
            "count": 1,
            "move_range": 12,
            "control_score": 1,
            "health": 4,
            "num_models": 3,
            "base_width": 2,    # oval base: 2.5" long
            "base_height": 2,   # and 1.5" wide
            "attacks": []
        },

        "Clawlord": {
            "count": 1,
            "move_range": 18,
            "control_score": 2,
            "health": 7,
            "num_models": 1,
            "base_width": 2,
            "base_height": 3,
            "attacks": []
        },

        "Grey Seer": {
            "count": 1,
            "move_range": 12,
            "control_score": 2,
            "health": 5,
            "num_models": 1,
            "base_width": 1.5,
            "base_height": 1.5,
            "attacks": []
        },

        "Warlock Engineer": {
            "count": 1,
            "move_range": 12,
            "control_score": 2,
            "health": 5,
            "num_models": 2,
            "base_width": 1.5,
            "base_height": 1.5,
            "attacks": []
        },
    }
