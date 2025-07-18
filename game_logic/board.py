import random
import math
from game_logic.units import Unit, Model
from game_logic.objective import Objective

BOARD_WIDTH = 60
BOARD_HEIGHT = 44

TILE_EMPTY = "-"
TILE_UNIT = "U"
TILE_TERRAIN = "T"
TILE_OBJECTIVE = "O"
TILE_PLAYER_1 = "1"
TILE_PLAYER_2 = "2"

class Board:
    def __init__(self, width=60, height=44):
        self.width = width
        self.height = height
        self.grid = [[TILE_EMPTY for _ in range(self.width)] for _ in range(self.height)]
        self.units = []
        self.objectives = []
        self.terrain = []

    def bases_touching(self, model_a: Model, model_b: Model) -> bool:
        """Return True if the two models are in base-to-base contact."""
        for ax, ay in model_a.get_occupied_squares():
            for bx, by in model_b.get_occupied_squares():
                if max(abs(ax - bx), abs(ay - by)) == 1 and (ax != bx or ay != by):
                    return True
        return False

    def units_base_to_base(self, unit_a: Unit, unit_b: Unit) -> bool:
        """Return True if any models from the two units are in base contact."""
        for m_a in unit_a.models:
            for m_b in unit_b.models:
                if self.bases_touching(m_a, m_b):
                    return True
        return False

    def models_overlap(self) -> bool:
        """Check if any models on the board occupy the same square."""
        occupied = set()
        for unit in self.units:
            for model in unit.models:
                for sq in model.get_occupied_squares():
                    if sq in occupied:
                        return True
                    occupied.add(sq)
        return False

    def place_objective(self, x, y):
        obj = Objective(x, y)
        self.objectives.append(obj)
        self.grid[y][x] = TILE_OBJECTIVE

    def is_valid_terrain_location(self, tiles):
        for x, y in tiles:
            if not (6 <= x < self.width - 6 and 6 <= y < self.height - 6):
                return False
            for ox, oy in self.terrain:
                if math.hypot(x - ox, y - oy) < 6:
                    return False
            for obj in self.objectives:
                if math.hypot(x - obj.x, y - obj.y) < 12:
                    return False
        return True

    def place_terrain_piece(self, x, y, rotated_shape):
        placed_tiles = [(x + dx, y + dy) for dx, dy in rotated_shape]
        for px, py in placed_tiles:
            if not (0 <= px < self.width and 0 <= py < self.height):
                return False
            if self.grid[py][px] != "-":
                return False
        for px, py in placed_tiles:
            self.terrain.append((px, py))
            self.grid[py][px] = "T"
        return True

    def place_unit(self, unit: Unit):
        """Place a unit on the board ensuring all models fit within bounds."""

        # Validate that all model squares are on the board and unoccupied
        pending = []
        for model in unit.models:
            for x, y in model.get_occupied_squares():
                if not (0 <= x < self.width and 0 <= y < self.height):
                    print("Placement out of bounds!")
                    return False
                if self.grid[y][x] != TILE_EMPTY:
                    print("Placement occupied!")
                    return False
                pending.append((x, y))

        # All squares valid, perform placement
        for x, y in pending:
            self.grid[y][x] = TILE_UNIT

        self.units.append(unit)
        print(f"{unit.name} placed successfully.")
        return True

    def get_path(self, start_x, start_y, end_x, end_y):
        path = []
        x1, y1 = start_x, start_y
        x2, y2 = end_x, end_y

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = -1 if x1 > x2 else 1
        sy = -1 if y1 > y2 else 1

        if dx > dy:
            err = dx / 2.0
            while x != x2:
                path.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y2:
                path.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

        path.append((x2, y2))
        return path

    def is_path_clear(self, start_x, start_y, end_x, end_y):
        """Check if the straight line between two points is unobstructed."""
        path = self.get_path(start_x, start_y, end_x, end_y)
        for x, y in path[1:-1]:  # ignore start and destination tiles
            if self.grid[y][x] not in (TILE_EMPTY, TILE_OBJECTIVE):
                return False
        return True

    def is_path_blocked(self, path, start_pos, unit=None):
        """Return True if any tile along ``path`` is blocked by terrain or other
        units.

        ``unit`` represents the moving unit and all squares occupied by this
        unit are ignored when checking for obstructions. This prevents the
        moving unit from being considered an obstacle to itself when it spans
        multiple board squares.
        """

        ignore_squares = set()
        if unit:
            for m in unit.models:
                ignore_squares.update(m.get_occupied_squares())

        for x, y in path:
            if (x, y) != start_pos:
                if self.grid[y][x] not in (TILE_EMPTY, TILE_OBJECTIVE):
                    if (x, y) in ignore_squares:
                        continue
                    return True, (x, y)
        return False, None

    def move_unit(self, unit: Unit, dest_x, dest_y):
        """Move the entire unit, keeping formation for all models."""

        if not (0 <= dest_x < BOARD_WIDTH and 0 <= dest_y < BOARD_HEIGHT):
            print("Move out of bounds!")
            return False

        dx = dest_x - unit.x
        dy = dest_y - unit.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance > unit.move_range:
            print(f"{unit.name} can't move that far (max {unit.move_range / 2:.1f} inches).")
            return False

        path = self.get_path(unit.x, unit.y, dest_x, dest_y)
        blocked, blocked_tile = self.is_path_blocked(path, (unit.x, unit.y), unit)
        if blocked:
            print(f"Path is blocked at {blocked_tile}.")
            return False

        # compute new positions for all models
        new_positions = []
        unit_squares = set()
        for m in unit.models:
            unit_squares.update(m.get_occupied_squares())

        for m in unit.models:
            new_x = m.x + dx
            new_y = m.y + dy
            new_sq = []
            w_tiles = int(round(m.base_width / 0.5))
            h_tiles = int(round(m.base_height / 0.5))
            for ddx in range(w_tiles):
                for ddy in range(h_tiles):
                    nx = new_x + ddx
                    ny = new_y + ddy
                    if not (0 <= nx < self.width and 0 <= ny < self.height):
                        print("Move out of bounds!")
                        return False
                    if self.grid[ny][nx] != TILE_EMPTY and (nx, ny) not in unit_squares:
                        print("Destination occupied!")
                        return False
                    new_sq.append((nx, ny))
            new_positions.append((new_x, new_y, new_sq))

        # clear current squares
        for m in unit.models:
            for x, y in m.get_occupied_squares():
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y][x] = TILE_EMPTY

        # apply new positions
        for idx, (new_x, new_y, new_sq) in enumerate(new_positions):
            for x, y in new_sq:
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y][x] = TILE_UNIT
            unit.models[idx].x = new_x
            unit.models[idx].y = new_y

        unit.x, unit.y = dest_x, dest_y

        print(f"{unit.name} moved to ({dest_x}, {dest_y}).")
        return True

    def move_model(self, unit: Unit, model_idx: int, dest_x: int, dest_y: int,
                   enforce_coherency: bool = True):
        """Move an individual model if the destination is valid.

        The ``enforce_coherency`` flag controls whether the normal coherency
        requirement (being within 2" of another model in the unit) is applied.
        This is useful during charges where models may temporarily break
        coherency while being repositioned.
        """
        if model_idx < 0 or model_idx >= len(unit.models):
            return False

        model = unit.models[model_idx]

        def _squares(x, y, width, height):
            occ = []
            w_tiles = int(round(width / 0.5))
            h_tiles = int(round(height / 0.5))
            for dx in range(w_tiles):
                for dy in range(h_tiles):
                    occ.append((x + dx, y + dy))
            return occ

        new_squares = _squares(dest_x, dest_y, model.base_width, model.base_height)
        current_squares = set(model.get_occupied_squares())
        unit_squares = set()
        for m in unit.models:
            unit_squares.update(m.get_occupied_squares())

        for x, y in new_squares:
            if not (0 <= x < self.width and 0 <= y < self.height):
                return False
            if self.grid[y][x] != TILE_EMPTY and (x, y) not in unit_squares:
                return False

        if enforce_coherency:
            coherent = False
            for i, other in enumerate(unit.models):
                if i == model_idx:
                    continue
                if math.sqrt((dest_x - other.x) ** 2 + (dest_y - other.y) ** 2) <= 2:
                    coherent = True
                    break
            if not coherent and len(unit.models) > 1:
                return False

        for x, y in current_squares:
            self.grid[y][x] = TILE_EMPTY
        for x, y in new_squares:
            self.grid[y][x] = TILE_UNIT

        model.x, model.y = dest_x, dest_y
        if model_idx == 0:
            unit.x, unit.y = dest_x, dest_y
        return True

    def ai_move(self, unit: Unit):
        print(f"AI's turn for {unit.name}")
        attempts = 10
        for _ in range(attempts):
            dx = random.randint(-unit.move_range, unit.move_range)
            dy = random.randint(-unit.move_range, unit.move_range)
            dest_x = unit.x + dx
            dest_y = unit.y + dy

            if not (0 <= dest_x < BOARD_WIDTH and 0 <= dest_y < BOARD_HEIGHT):
                continue

            dist = math.sqrt(dx**2 + dy**2)
            if dist <= unit.move_range:
                if self.move_unit(unit, dest_x, dest_y):
                    return
        print(f"{unit.name} could not move after {attempts} attempts.")

    def update_objective_control(self):
        for obj in self.objectives:
            obj.update_control(self.units)

    def display_objective_status(self):
        print("\nObjective Control Status:")
        for obj in self.objectives:
            owner = f"Team {obj.control_team}" if obj.control_team else "Uncontrolled"
            print(f" - Objective at ({obj.x}, {obj.y}) is controlled by {owner}.")