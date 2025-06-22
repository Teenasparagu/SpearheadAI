# SpearheadAI

This project provides a basic game engine. A lightweight Flask application is

included that only displays the current board state while the game itself is run
from a separate command line program.

## Launching the Board Viewer


1. Install dependencies (Flask, numpy, and pytest are used):
   ```bash
   pip install -r requirements.txt
   ```

2. Start the viewer in one terminal:

   ```bash
   python run_game.py
   ```

   Then open `http://localhost:5000/` in your browser to see the board.
3. In another terminal run the CLI game:
   ```bash
   python run_game.py
   ```
   The CLI prompts for input while the web page updates to reflect the board
   state.


## Programmatic Usage

You can interact with the game directly via `GameEngine` and the helper
functions in `game_logic.game_engine`.

Example deploying forces and taking a single move:

```python
from game_logic.game_engine import GameEngine, run_deployment_phase

engine = GameEngine()

responses = iter(["first"])  # answers the first-turn prompt

def get_input(prompt):
    return next(responses)

# simple logger
log = print

run_deployment_phase(engine.game_state, engine.board, get_input, log)

# move the first player unit one square east
unit = engine.game_state.units["player"][0]
engine.board.move_unit(unit, unit.x + 1, unit.y)
```

This snippet mirrors the behaviour exercised in the unit tests and can be used
as a starting point for custom scripts.
