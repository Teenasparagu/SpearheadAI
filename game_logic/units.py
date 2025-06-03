import importlib
import math

class Model:
    def __init__(self, x, y, max_health=1, base_diameter=1.0):
        self.x = x
        self.y = y
        self.max_health = max_health
        self.current_health = max_health
        self.base_diameter = base_diameter
        self.ranged_attacks = []

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
        radius_in_tiles = int(round(radius / 0.5))

        for dx in range(-radius_in_tiles, radius_in_tiles + 1):
            for dy in range(-radius_in_tiles, radius_in_tiles + 1):
                dist = math.sqrt(dx**2 + dy**2)
                if dist <= radius_in_tiles + 0.01:
                    occupied.append((self.x + dx, self.y + dy))
        return occupied

    def __repr__(self):
        return f"Model({self.x}, {self.y}, base={self.base_diameter}\")"


class Unit:
    def __init__(self, name, faction, team, num_models=5, control_score=None, x=None, y=None, unit_data=None):
        self.name = name
        self.faction = faction
        self.team = team
        self.num_models = num_models
        self.has_run = False

        self.x = x if x is not None else 3
        self.y = y if y is not None else 3

        if unit_data is None:
            faction_module = importlib.import_module(f"game_logic.factions.{faction}")
            unit_data = faction_module.unit_definitions.get(name)
            if not unit_data:
                raise ValueError(f"Unit '{name}' not found in faction '{faction}'")

        self.move_range = unit_data.get("move_range", 6)
        self.control_score = control_score if control_score is not None else unit_data.get("control_score", 1)
        self.base_width = unit_data.get("base_width", 1.0)
        self.base_height = unit_data.get("base_height", 1.0)
        model_health = unit_data.get("health", 1)

        self.ranged_attacks = unit_data.get("range", [])
        self.melee_weapons = unit_data.get("melee_weapons", [])

        leader_x = self.x
        leader_y = self.y
        base_diameter = max(self.base_width, self.base_height)

        self.models = [Model(leader_x, leader_y, max_health=model_health, base_diameter=base_diameter)]

        placed_positions = {(leader_x, leader_y)}
        ring_radius = 1
        model_index = 1

        while model_index < self.num_models:
            for dx in range(-ring_radius, ring_radius + 1):
                for dy in range(-ring_radius, ring_radius + 1):
                    new_x = leader_x + dx
                    new_y = leader_y + dy
                    if (new_x, new_y) not in placed_positions:
                        placed_positions.add((new_x, new_y))
                        self.models.append(Model(new_x, new_y, max_health=model_health, base_diameter=base_diameter))
                        model_index += 1
                        if model_index >= self.num_models:
                            break
                if model_index >= self.num_models:
                    break
            ring_radius += 1

        for i, model in enumerate(self.models):
            model.ranged_attacks = [atk for atk in self.ranged_attacks if atk.get("model_index") is None or atk.get("model_index") == i]

    def position(self):
        return self.x, self.y

    def __repr__(self):
        return f"{self.name} (Team {self.team})"

    def display(self):
        print(f"Unit: {self.name} (Team {self.team})")
        for i, model in enumerate(self.models):
            label = "Leader" if i == 0 else f"Model {i}"
            print(f" - {label} at ({model.x}, {model.y}) | Base: {model.base_diameter}\"")

    def model_count(self):
        return len(self.models)

    def apply_damage(self, dmg):
        for model in self.models:
            if model.is_alive():
                model.take_damage(dmg)
                print(f"{self.name}: Model took {dmg} damage (HP: {model.current_health}/{model.max_health})")
                if not model.is_alive():
                    print(f"{self.name}: A model has been slain!")
                    self.models.remove(model)
                break
        print(f"{self.name}: {len(self.models)} model(s) remaining.")

def is_in_combat(x, y, board, team, radius=6):
    for enemy_unit in board.units:
        if enemy_unit.team != team:
            for model in enemy_unit.models:
                if math.sqrt((x - model.x)**2 + (y - model.y)**2) < radius:
                    return True
    return False