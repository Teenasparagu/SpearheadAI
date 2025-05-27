from game_logic.units import Unit
from .faction_factory import FactionFactory

class StormcastFactory(FactionFactory):
    faction_name= "stormcast"
    unit_definitions = {
        "Liberators": {
            "count": 1,
            "move_range": 10,
            "control_score": 2,
            "health": 2,
            "num_models" : 5,
            "base_width": 1.5,
            "base_height": 1.5,
            "attacks": []
        },

        "Prosecutors": {
            "count": 1,
            "move_range": 24,
            "control_score": 1,
            "health": 2,
            "num_models" : 3,
            "base_width": 1.5,
            "base_height": 1.5,
            "attacks": [
                {
                    "name": "Stormcall Javelin",
                    "range": 10,
                    "attacks": 1,
                    "to_hit": 3,
                    "to_wound": 3,
                    "rend": 1,
                    "damage": "D3",
                    "keywords": []
                }
            ]
        },

        "Lord-Veritant": {
            "count": 1,
            "move_range": 10,
            "control_score": 2,
            "health": 6,
            "num_models": 1,
            "base_width": 1.5,   # in inches
            "base_height": 1.5,   # use 2.0 or 2.5 for cavalry/mounted units
            "attacks": []
        },

        "Lord-Vigilant": {
            "count": 1,
            "move_range": 24,
            "control_score": 2,
            "health": 8,
            "num_models": 1,
            "base_width": 2.0,   # in inches
            "base_height": 3.5,   # use 2.0 or 2.5 for cavalry/mounted units
            "attacks": []
        },
        
    }