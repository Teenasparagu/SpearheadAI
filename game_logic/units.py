import importlib
import math
from dataclasses import dataclass, field


@dataclass
class Model:
    x: int
    y: int
    max_health: int = 1
    base_width: float = 1.0
    base_height: float = 1.0
    ranged_attacks: list = field(default_factory=list)
    current_health: int = field(init=False)

    @property
    def base_diameter(self) -> float:
        """Largest dimension of the model's base."""
        return max(self.base_width, self.base_height)

    def __post_init__(self):
        self.current_health = self.max_health

    def is_alive(self):
        return self.current_health > 0

    def take_damage(self, dmg):
        self.current_health -= dmg
        if self.current_health < 0:
            self.current_health = 0

    def position(self):
        return self.x, self.y

    def get_occupied_squares(self):
        """Return the board squares occupied by this model."""
        occupied = []
        width_tiles = int(round(self.base_width / 0.5))
        height_tiles = int(round(self.base_height / 0.5))

        for dx in range(width_tiles):
            for dy in range(height_tiles):
                occupied.append((self.x + dx, self.y + dy))
        return occupied

    def get_display_squares(self):
        """Return squares representing a circular or elliptical base."""
        occupied = []
        width_tiles = int(round(self.base_width / 0.5))
        height_tiles = int(round(self.base_height / 0.5))

        cx = width_tiles / 2.0
        cy = height_tiles / 2.0
        rx = width_tiles / 2.0
        ry = height_tiles / 2.0

        for dx in range(width_tiles):
            for dy in range(height_tiles):
                px = dx + 0.5
                py = dy + 0.5
                if ((px - cx) ** 2) / (rx ** 2) + ((py - cy) ** 2) / (ry ** 2) <= 1:
                    occupied.append((self.x + dx, self.y + dy))
        return occupied

    def get_central_square(self):
        """Return the central board square for this model."""
        width_tiles = int(round(self.base_width / 0.5))
        height_tiles = int(round(self.base_height / 0.5))

        cx = width_tiles // 2
        cy = height_tiles // 2
        if width_tiles % 2 == 0:
            cx -= 1
        if height_tiles % 2 == 0:
            cy -= 1
        return (self.x + cx, self.y + cy)

    def __repr__(self):
        return (
            f"Model({self.x}, {self.y}, base_width={self.base_width}, "
            f"base_height={self.base_height})"
        )


@dataclass
class Unit:
    name: str
    faction: str
    team: int
    num_models: int = 5
    control_score: int = 1
    x: int = 3
    y: int = 3
    unit_data: dict | None = None
    move_range: int = 6
    base_width: float = 1.0
    base_height: float = 1.0
    ranged_attacks: list = field(default_factory=list)
    melee_weapons: list = field(default_factory=list)
    models: list = field(default_factory=list)
    has_run: bool = False
    keywords: list = field(default_factory=list)

    def __post_init__(self):
        unit_data = self.unit_data
        if unit_data is None:
            faction_module = importlib.import_module(f"game_logic.factions.{self.faction}")
            unit_data = faction_module.unit_definitions.get(self.name)
            if not unit_data:
                raise ValueError(f"Unit '{self.name}' not found in faction '{self.faction}'")
            self.unit_data = unit_data

        self.move_range = unit_data.get("move_range", self.move_range)
        self.control_score = unit_data.get("control_score", self.control_score)
        self.base_width = unit_data.get("base_width", self.base_width)
        self.base_height = unit_data.get("base_height", self.base_height)
        model_health = unit_data.get("health", 1)

        self.ranged_attacks = unit_data.get("range", [])
        self.melee_weapons = unit_data.get("melee_weapons", [])
        self.keywords = unit_data.get("keywords", self.keywords)

        leader_x = self.x
        leader_y = self.y

        self.models = [Model(leader_x, leader_y, max_health=model_health,
                             base_width=self.base_width, base_height=self.base_height)]

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
                        self.models.append(Model(new_x, new_y,
                                                max_health=model_health,
                                                base_width=self.base_width,
                                                base_height=self.base_height))
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
        """Apply damage to the first alive model in the unit."""
        for model in list(self.models):
            if model.is_alive():
                model.take_damage(dmg)
                print(
                    f"{self.name}: Model took {dmg} damage (HP: {model.current_health}/{model.max_health})"
                )
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
