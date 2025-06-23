"""Faction definitions for Stormcast forces."""

try:  # pragma: no cover - allow running as a script
    from ..units import Unit
    from .faction_factory import FactionFactory
except ImportError:  # fallback when executed directly
    import os
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from game_logic.units import Unit
    from game_logic.factions.faction_factory import FactionFactory

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
            "range": [],
            "melee_weapons": [
            {
            "name": "Warhammer",
            "attacks": 2,
            "to_hit": 3,
            "to_wound": 3,
            "rend": 1,
            "damage": 1
            },
            ]
        },

        "Prosecutors": {
            "count": 1,
            "move_range": 24,
            "control_score": 1,
            "health": 2,
            "num_models" : 3,
            "base_width": 1.5,
            "base_height": 1.5,
            "range": [
                {
                    "name": "Stormcall Javelin",
                    "range": 20,
                    "attacks": 1,
                    "to_hit": 3,
                    "to_wound": 3,
                    "rend": 1,
                    "damage": "D3",
                    "keywords": []
                }
            ],
            "melee_weapons": [
            {
            "name": "Stormcall Javelin",
            "attacks": 3,
            "to_hit": 3,
            "to_wound": 3,
            "rend": 1,
            "damage": 1
            },
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
            "range": [],
            "melee_weapons": [
            {
            "name": "Staff of Abjuration",
            "attacks": 1,
            "to_hit": 3,
            "to_wound": 3,
            "rend": 1,
            "damage": 3
            },
            {
            "name": "Judgement Blade",
            "attacks": 3,
            "to_hit": 3,
            "to_wound": 3,
            "rend": 1,
            "damage": "d3"
            },
            ]
        },

        "Lord-Vigilant": {
            "count": 1,
            "move_range": 24,
            "control_score": 2,
            "health": 8,
            "num_models": 1,
            "base_width": 2.0,   # in inches
            "base_height": 3.5,   # use 2.0 or 2.5 for cavalry/mounted units
            "range": [],
            "melee_weapons": [
            {
            "name": "Hallowed Greataxe",
            "attacks": 5,
            "to_hit": 3,
            "to_wound": 3,
            "rend": 2,
            "damage": 2
            },
            {
            "name": "Gryph-Stalker's Beak and Talons",
            "attacks": 3,
            "to_hit": 4,
            "to_wound": 3,
            "rend": 1,
            "damage": 2
            },
            ]
            
        },
        
    }