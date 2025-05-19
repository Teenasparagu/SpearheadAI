import importlib
import math

class Model:
    def __init__(self, x, y, max_health=1, base_diameter=1.0):
        self.x = x
        self.y = y
        self.max_health = max_health
        self.current_health = max_health
        self.base_diameter = base_diameter  # in inches

    def is_alive(self):
        return self.current_health > 0

    def take_damage(self, dmg):
        self.current_health -= dmg
        if self.current_health < 0:
            self.current_health = 0

    def position(self):
        return self.x, self.y

    def get_occupied_squares(self):
        occupied = []
        radius = self.base_diameter / 2.0
        radius_in_tiles = int(round(radius / 0.5))  # each tile = 0.5 inches

        for dx in range(-radius_in_tiles, radius_in_tiles + 1):
            for dy in range(-radius_in_tiles, radius_in_tiles + 1):
                dist = math.sqrt(dx**2 + dy**2)
                if dist <= radius_in_tiles + 0.01:
                    occupied.append((self.x + dx, self.y + dy))
        return occupied

    def __repr__(self):
        return f"Model({self.x}, {self.y}, base={self.base_diameter}\")"

class Unit:
    def __init__(self, name, x, y, faction, team, num_models=5, control_score=None):
        self.name = name
        self.faction = faction
        self.team = team
        self.x = x
        self.y = y
        self.num_models = num_models
        self.has_run = False

        # Import faction data
        faction_module = importlib.import_module(f"game_logic.factions.{faction}")
        unit_data = faction_module.unit_definitions.get(name)

        if not unit_data:
            raise ValueError(f"Unit '{name}' not found in faction '{faction}'")

        # Set stats from faction file, with default fallbacks
        self.move_range = unit_data.get("move_range", 6)
        self.control_score = control_score if control_score is not None else unit_data.get("control_score", 1)
        self.base_diameter = unit_data.get("base_diameter", 1.0)
        model_health = unit_data.get("health", 1)

        # Create models
        self.models = [Model(x, y, max_health=model_health, base_diameter=self.base_diameter)]  # Leader
        for i in range(1, num_models):
            offset_x = (i % 3) - 1
            offset_y = (i // 3) - 1
            self.models.append(Model(x + offset_x, y + offset_y, max_health=model_health, base_diameter=self.base_diameter))

    def position(self):
        return self.x, self.y

    def __repr__(self):
        return f"{self.name} (Team {self.team})"

    def display(self):
        print(f"Unit: {self.name} (Team {self.team})")
        for i, model in enumerate(self.models):
            label = "Leader" if i == 0 else f"Model {i}"
            print(f" - {label} at ({model.x}, {model.y}) | Base: {model.base_diameter}\"")

    def apply_damage(self, dmg):
        for model in self.models:
            if model.is_alive():
                model.take_damage(dmg)
                print(f"{self.name}: Model took {dmg} damage (HP: {model.current_health}/{model.max_health})")
                if not model.is_alive():
                    print(f"{self.name}: A model has been slain!")
                    self.models.remove(model)
                break  # Only one model takes damage at a time
        print(f"{self.name}: {len(self.models)} model(s) remaining.")

    def model_count(self):
        return len(self.models)
