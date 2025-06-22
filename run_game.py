"""Run the CLI game and launch the board viewer."""

from threading import Thread
from app import app, engine


def _start_viewer() -> None:
    """Run the Flask viewer in a background thread."""
    app.run(use_reloader=False)


def main() -> None:
    print("Starting viewer at http://localhost:5000/")
    viewer_thread = Thread(target=_start_viewer, daemon=True)
    viewer_thread.start()
    engine.run_game(get_input=input, log=print)


if __name__ == "__main__":
    main()

