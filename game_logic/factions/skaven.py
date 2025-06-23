"""Faction definitions for Skaven forces."""

try:  # pragma: no cover - allow running as a script
    from ..units import Unit
    from .faction_factory import FactionFactory
except ImportError:  # fallback when executed directly
    import os
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from game_logic.units import Unit
    from game_logic.factions.faction_factory import FactionFactory

class SkavenFactory(FactionFactory):
    faction_name= "skaven"
    unit_definitions = {
        "Clanrats": {
            "count": 2,
            "move_range": 12,
            "control_score": 1,
            "health": 1,  
            "num_models": 10,
            "base_width": 1.0,
            "base_height": 1.0,
            "range": [],
            "melee_weapons": [
            {
            "name": "Rusty Blade",
            "attacks": 2,
            "to_hit": 4,
            "to_wound": 5,
            "rend": 0,
            "damage": 1
            },
            ],
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
            ],
            "melee_weapons": [
            {
            "name": "Claws, Blades and Fangs",
            "attacks": 5,
            "to_hit": 4,
            "to_wound": 3,
            "rend": 1,
            "damage": 2
            },
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
        "range": [  
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
        ],
        "melee_weapons": [
        {
        "name": "Warpforged Halberd",
        "attacks": 5,
        "to_hit": 3,
        "to_wound": 4,
        "rend": 1,
        "damage": 2
        },
        {
        "name": "Gnaw-beast's Chisel Fangs",
        "attacks": 4,    
        "to_hit": 4,
        "to_wound": 3,
        "rend": 1,
        "damage": "d3"
        }
        ],
        },

        "Grey Seer": {
            "count": 1,
            "move_range": 12,
            "control_score": 2,
            "health": 5,
            "num_models": 1,
            "base_width": 1.5,
            "base_height": 1.5,
            "range": [],
            "melee_weapons": [
            {
            "name": "Warpstone Staff",
            "attacks": 3,
            "to_hit": 4,
            "to_wound": 4,
            "rend": 1,
            "damage": "d3"
            },
            ]
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
            ],
            "melee_weapons": [
            {
            "name": "Warpforged Dagger",
            "attacks": 3,
            "to_hit": 4,
            "to_wound": 4,
            "rend": 0,
            "damage": 2
            },
            ]
        },
    }
