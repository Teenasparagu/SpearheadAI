web_interface
from game_logic.game_engine import GameEngine


def main() -> None:
    """Entry point for running the game via the command line."""

    engine = GameEngine()
    engine.run_game(get_input=input, log=print)


if __name__ == "__main__":
    main()
