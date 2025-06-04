"""Entry point for the Spearhead skirmish game."""

import random

from game_logic.board import Board
from game_phases.movement_phase import (
    player_movement_phase,
    ai_movement_phase,
)
from game_phases.charge_phase import charge_phase, ai_charge_phase
from game_phases.deployment import deployment_phase
from game_phases.victory_phase import (
    process_end_phase_actions,
    calculate_victory_points,
)
from game_phases.shooting_phase import player_shooting_phase
from game_phases.combat_phase import combat_phase


class Game:
    """Handle overall game flow."""

    def __init__(self) -> None:
        print("Welcome to Spearhead: Skirmish for the Realms!")
        print("==============================================")
        print("The battlefield awaits your command.\n")

        self.board = Board(width=60, height=44)
        self.total_vp = {1: 0, 2: 0}
        self.player_units, self.ai_units, self.current_priority = deployment_phase(
            self.board
        )

    def run(self) -> None:
        """Play four rounds of the game."""
        for round_num in range(1, 5):
            print(f"\n=== Round {round_num} Begins ===")
            if round_num > 1:
                self._roll_off()

            if self.current_priority == "player":
                self.player_turn()
                self.ai_turn()
            else:
                self.ai_turn()
                self.player_turn()

        self._final_results()

    # ------------------------------------------------------------------
    # Phase helpers
    def _roll_off(self) -> None:
        """Determine priority for the round."""
        print("\nRolling off for priority...")
        player_roll = random.randint(1, 6)
        ai_roll = random.randint(1, 6)
        print(f"You rolled a {player_roll}, AI rolled a {ai_roll}")

        if player_roll > ai_roll:
            choice = input(
                "You win the roll-off. Go first or second? (first/second): "
            ).strip().lower()
            self.current_priority = "player" if choice == "first" else "ai"
        elif ai_roll > player_roll:
            self.current_priority = random.choice(["player", "ai"])
            print(
                f"AI wins the roll-off and chooses to go {'first' if self.current_priority == 'ai' else 'second'}."
            )
        else:
            print("It's a tie! Player retains priority.")

    def player_turn(self) -> None:
        """Execute a player turn."""
        print("\n-- Player Turn --")
        self._objective_check()
        player_movement_phase(self.board, self.player_units)
        player_shooting_phase(self.board, self.player_units, self.ai_units)
        charge_phase(self.board, self.player_units)
        combat_phase(
            self.board,
            current_team=1,
            player_units=self.player_units,
            ai_units=self.ai_units,
        )
        process_end_phase_actions(self.board, self.player_units)
        self._objective_check()
        calculate_victory_points(self.board, self.total_vp, scoring_team=1)

    def ai_turn(self) -> None:
        """Execute the AI turn."""
        print("\n-- AI Turn --")
        self._objective_check()
        ai_movement_phase(self.board, self.ai_units)
        ai_charge_phase(self.board, self.ai_units, self.player_units)
        combat_phase(
            self.board,
            current_team=1,
            player_units=self.player_units,
            ai_units=self.ai_units,
        )
        process_end_phase_actions(self.board, self.ai_units)
        self._objective_check()
        calculate_victory_points(self.board, self.total_vp, scoring_team=2)

    def _objective_check(self) -> None:
        self.board.update_objective_control()
        self.board.display_objective_status()

    def _final_results(self) -> None:
        """Display final VP totals."""
        print("\n=== Game Over ===")
        print(
            f"Final Victory Points:\n  Player 1: {self.total_vp[1]}\n  Player 2: {self.total_vp[2]}"
        )
        if self.total_vp[1] > self.total_vp[2]:
            print(">> Player 1 wins!")
        elif self.total_vp[2] > self.total_vp[1]:
            print(">> Player 2 wins!")
        else:
            print(">> It's a tie!")



def main() -> None:
    """Script entry point."""
    Game().run()


if __name__ == "__main__":
    main()
