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
        for model in unit.models:
            for x, y in model.get_occupied_squares():
                if not (0 <= x < self.width and 0 <= y < self.height):
                    print(f"{unit.name} placement failed: model at ({x}, {y}) is out of bounds.")
                    return False
                if self.grid[y][x] != TILE_EMPTY:
                    print(f"{unit.name} placement failed: tile ({x}, {y}) is already occupied.")
                    return False

        for i, model in enumerate(unit.models):
            coherent = False
            for j, other in enumerate(unit.models):
                if i != j:
                    dist = math.sqrt((model.x - other.x)**2 + (model.y - other.y)**2)
                    if dist <= 2:
                        coherent = True
                        break
            if not coherent:
                print(f"Model at ({model.x}, {model.y}) is not within 1\" of any other model in the unit.")
                return False

        self.units.append(unit)
        for model in unit.models:
            for x, y in model.get_occupied_squares():
                self.grid[y][x] = TILE_UNIT

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
        for x, y in path:
            if (x, y) != start_pos:
                if self.grid[y][x] not in (TILE_EMPTY, TILE_OBJECTIVE):
                    if unit and any(model.x == x and model.y == y for model in unit.models):
                        continue
                    return True, (x, y)
        return False, None

    def move_unit(self, unit: Unit, dest_x, dest_y):
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

        self.grid[unit.y][unit.x] = TILE_EMPTY
        unit.x, unit.y = dest_x, dest_y
        unit.models[0].x, unit.models[0].y = dest_x, dest_y

        print(f"{unit.name} moved to ({dest_x}, {dest_y}).")
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