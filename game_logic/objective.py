import math
from dataclasses import dataclass


@dataclass
class Objective:
    x: int
    y: int
    control_team: int | None = None

    def get_control_team(self, units):
        control_player_1 = 0
        control_player_2 = 0

        for unit in units:
            for model in unit.models:
                distance = math.sqrt((model.x - self.x)**2 + (model.y - self.y)**2)
                if distance <= 12:  # 6 inches in 0.5" tiles
                    if unit.team == 1:
                        control_player_1 += unit.control_score
                    elif unit.team == 2:
                        control_player_2 += unit.control_score

        if control_player_1 > control_player_2:
            return 1
        elif control_player_2 > control_player_1:
            return 2
        else:
            return None

    def update_control(self, units):
        current_team = self.get_control_team(units)
        if current_team is not None and current_team != self.control_team:
            self.control_team = current_team

    def __repr__(self):
        return f"Objective(x={self.x}, y={self.y}, controlled_by={self.control_team})"