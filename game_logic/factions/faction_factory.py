"""Base factory for building faction forces."""

try:  # pragma: no cover - allow running as a script
    from ..units import Unit
except ImportError:  # fallback when executed directly
    import os
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from game_logic.units import Unit

class FactionFactory:
    faction_name = None
    unit_definitions = {}

    def create_force(self, team):
        force = []
        for unit_name, config in self.unit_definitions.items():
            count = config.get("count", 1)
            for i in range(count):
                name_suffix = f" {chr(65+i)}" if count > 1 else ""
                unit = Unit(
                    name=unit_name + name_suffix,
                    faction=self.faction_name,
                    team=team,
                    num_models=config["num_models"],
                    control_score=config.get("control_score", 1),
                    unit_data=config
                )
                unit.attacks = config.get("attacks", [])
                force.append(unit)
        return force
