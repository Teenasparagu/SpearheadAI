import math

class Objective:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.control_team = None

    def get_control_team(self, units):
        control_player_1 = 0
        control_player_2 = 0

        # Iterate over all units to calculate control score
        for unit in units:
            # Check if any models are within 6 inches of the objective
            for model in unit.models:
                distance = math.sqrt((model.x - self.x)**2 + (model.y - self.y)**2)
                if distance <= 12:  # 
                    if unit.team == 1:
                        control_player_1 += 1  # Add control score for Player 1
                    elif unit.team == 2:
                        control_player_2 += 1  # Add control score for Player 2

        # Determine which player controls the objective
        if control_player_1 > control_player_2:
            return 1  # Player 1 controls the objective
        elif control_player_2 > control_player_1:
            return 2  # Player 2 controls the objective
        else:
            return None  # No team controls the objective
        
        
    def update_control(self, units):
        new_control_team = self.get_control_team(units)

        # If control has changed, print the update
        if new_control_team != self.control_team:
            if new_control_team:
                print(f"Objective at ({self.x}, {self.y}) is now controlled by Team {new_control_team}!")
            else:
                print(f"Objective at ({self.x}, {self.y}) is now uncontrolled.")
            
    def __repr__(self):
        return f"Objective(x={self.x}, y={self.y}, controlled_by={self.control_team})"
