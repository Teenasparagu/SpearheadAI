"""CLI runner that also launches the live board viewer."""
from threading import Thread
from app import app, engine


def _start_viewer() -> None:
    """Run the Flask board viewer without the reloader."""
    app.run(debug=False, use_reloader=False)


def main() -> None:
    # Launch the Flask viewer in a background thread so the CLI can run
    viewer = Thread(target=_start_viewer, daemon=True)
    viewer.start()

    engine.run_game(get_input=input, log=print)


if __name__ == "__main__":
    main()

