
def print_unit_positions(units):
    for unit in units:
        print(f"\n{unit.name} (Team {unit.team}) positions:")
        for i, model in enumerate(unit.models):
            label = "Leader" if i == 0 else f"Model {i}"
            print(f" - {label} at ({model.x}, {model.y})")

def print_objective_status(objectives):
    for obj in objectives:
        team = obj.control_team or "No team"
        print(f"Objective at ({obj.x}, {obj.y}) is controlled by: {team}")
