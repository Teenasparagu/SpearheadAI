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
            "range": []
        },
        
        "Rat Ogors": {
            "count": 1,
            "move_range": 12,
            "control_score": 1,
            "health": 4,
            "num_models": 3,
            "base_width": 2,    # oval base: 2.5" long
            "base_height": 2,   # and 1.5" wide
            "range": [
                {
                "model_index": 0,  # only the leader (index 0) has this weapon
                "name": "Warpfire Gun",
                "range": 20,
                "attacks": "2D6",
                "to_hit": 2,
                "to_wound": 4,
                "rend": 2,
                "damage": 1,
                "keywords": ["shoot_in_combat"]
            }
            ]
        },

        "Clawlord": {
        "count": 1,
        "move_range": 18,
        "control_score": 2,
        "health": 7,
        "num_models": 1,
        "base_width": 2,
        "base_height": 3,
        "range": [  # <- renamed from "range" to match expected attribute
            {
                "name": "Ratling Pistol",
                "range": 20,
                "attacks": "D6",  # random attacks
                "to_hit": 3,
                "to_wound": 3,
                "rend": 1,
                "damage": 1,
                "keywords": ["shoot_in_combat", "crit_auto_wound"]
            }
        ]
        },

        "Grey Seer": {
            "count": 1,
            "move_range": 12,
            "control_score": 2,
            "health": 5,
            "num_models": 1,
            "base_width": 1.5,
            "base_height": 1.5,
            "range": []
        },

        "Warlock Engineer": {
            "count": 1,
            "move_range": 12,
            "control_score": 2,
            "health": 5,
            "num_models": 2,
            "base_width": 1.5,
            "base_height": 1.5,
            "range": [
                {
                "name": "warplock Musket",
                "range": 48,
                "attacks": 2,
                "to_hit": 3,
                "to_wound": 3,
                "rend": 2,
                "damage": "D3",
                "keywords": ["crit_auto_wound"]
            }
            ]
        },
    }
