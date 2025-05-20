
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

def is_within_3_inches(x, y, all_models):
    for model in all_models:
        dist = math.sqrt((x - model.x)**2 + (y - model.y)**2)
        if dist < 3:
            return True
    return False

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

    def place_terrain(self, x, y):
        self.grid[y][x] = TILE_TERRAIN

    def place_unit(self, unit: Unit):
        # Check leader position
        if not (0 <= unit.x < self.width and 0 <= unit.y < self.height):
            print(f"Invalid position for {unit.name}: ({unit.x}, {unit.y})")
            return

        # Check if all model positions are valid and non-overlapping
        for model in unit.models:
            for x, y in model.get_occupied_squares():
                if not (0 <= x < self.width and 0 <= y < self.height):
                    print(f"Model at ({x}, {y}) out of bounds.")
                    return
                if self.grid[y][x] != TILE_EMPTY:
                    print(f"Tile at ({x}, {y}) is already occupied.")
                    return

        # Enforce 1" coherency (2-tile radius) from any other model in unit
        for i, model in enumerate(unit.models):
            coherent = False
            for j, other in enumerate(unit.models):
                if i != j:
                    dist = math.sqrt((model.x - other.x)**2 + (model.y - other.y)**2)
                    if dist <= 2:  # 1 inch = 2 tiles
                        coherent = True
                        break
            if not coherent:
                print(f"Model at ({model.x}, {model.y}) is not within 1\" of any other model in the unit.")
                return

        # If all checks pass, place unit
        self.units.append(unit)
        for model in unit.models:
            for x, y in model.get_occupied_squares():
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y][x] = TILE_UNIT

        print(f"{unit.name} placed successfully.")


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

    def is_path_blocked(self, path, start_pos, unit=None):
        for x, y in path:
            if (x, y) != start_pos:
                if self.grid[y][x] not in (TILE_EMPTY, TILE_OBJECTIVE):
                    if unit and any(model.x == x and model.y == y for model in unit.models):
                        continue
                    return True, (x, y)
        return False, None

    def move_unit(self, unit: Unit, dest_x, dest_y, confirm=False, check_range=True):
        if not (0 <= dest_x < BOARD_WIDTH and 0 <= dest_y < BOARD_HEIGHT):
            print("Move out of bounds!")
            return False

        dx = dest_x - unit.x
        dy = dest_y - unit.y
        distance = math.sqrt(dx**2 + dy**2)

        if check_range and distance > unit.move_range:
            print(f"{unit.name} can't move that far (max {unit.move_range / 2:.1f} inches).")
            return False


        path = self.get_path(unit.x, unit.y, dest_x, dest_y)
        blocked, blocked_tile = self.is_path_blocked(path, (unit.x, unit.y), unit)
        if blocked:
            print(f"Path is blocked at {blocked_tile}.")
            return False

        self.grid[unit.y][unit.x] = TILE_EMPTY

        # Move leader
        unit.x, unit.y = dest_x, dest_y
        unit.models[0].x, unit.models[0].y = dest_x, dest_y

        all_other_models = [m for u in self.units for m in u.models if u != unit]

        # Default triangle pattern around leader
        proposed_positions = []
        for i in range(1, len(unit.models)):
            offset_x = (i % 3) - 1
            offset_y = (i // 3) - 1
            model_x = dest_x + offset_x
            model_y = dest_y + offset_y
            proposed_positions.append((model_x, model_y))

        if confirm:
            print("Proposed model placements:")
            for i, pos in enumerate(proposed_positions, start=1):
                print(f" - Model {i}: {pos}")

            decision = input("Are you happy with these placements? (yes/no): ").strip().lower()
            if decision not in ["yes", "y"]:
                proposed_positions = []
                placed_positions = [(dest_x, dest_y)]  # Leader position

                for i in range(1, len(unit.models)):
                    while True:
                        try:
                            user_input = input(f"Enter position for Model {i} (x y): ")
                            x, y = map(int, user_input.strip().split())

                            if not (0 <= x < self.width and 0 <= y < self.height):
                                print("Position out of bounds. Try again.")
                                continue

                            dist_from_leader = math.sqrt((x - dest_x)**2 + (y - dest_y)**2)
                            if dist_from_leader > unit.move_range:
                                print("Too far from leader. Try again.")
                                continue

                            # Build a list of current checks including previous placements
                            current_check_list = all_other_models + [Model(px, py) for px, py in placed_positions]

                            if is_within_3_inches(x, y, current_check_list):
                                print("Too close to another model. Try again.")
                                continue

                            proposed_positions.append((x, y))
                            placed_positions.append((x, y))
                            break
                        except ValueError:
                            print("Invalid input. Use format: x y")

        # Apply model positions
        for i, (x, y) in enumerate(proposed_positions, start=1):
            unit.models[i].x = x
            unit.models[i].y = y

        for model in unit.models:
            if 0 <= model.x < self.width and 0 <= model.y < self.height:
                self.grid[model.y][model.x] = TILE_UNIT

        print(f"{unit.name} moved to ({dest_x}, {dest_y}).")
        return True

    def is_within_3_inches(x, y, other_models, radius=2):  # radius = 1 inch in squares
        for model in other_models:
            if math.sqrt((x - model.x)**2 + (y - model.y)**2) < radius:
                return True
        return False


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
