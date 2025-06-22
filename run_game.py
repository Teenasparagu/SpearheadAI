
"""CLI runner that shares the engine with the live board viewer."""
from app import engine


def main() -> None:
    engine.run_game(get_input=input, log=print)


if __name__ == "__main__":
    main()

