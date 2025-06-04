# SpearheadAI

This project provides a basic game engine with a simple Flask UI.

## Launching the Flask UI

1. Install dependencies (Flask, numpy, and pytest are used):
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app.py
   ```
   Then open `http://localhost:5000/game` in your browser and follow the prompts.

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
