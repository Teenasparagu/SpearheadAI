from game_logic.game_engine import GameEngine, run_deployment_phase


def main() -> None:
    print("Welcome to Spearhead: Skirmish for the Realms!")
    print("==============================================")
    print("The battlefield awaits your command.\n")

    engine = GameEngine()
    run_deployment_phase(engine.game_state, engine.board, input, print)

    for _ in range(1, 5):
        engine.run_round(input, print)

    print("\n=== Game Over ===")
    print(
        f"Final Victory Points:\n  Player 1: {engine.game_state.total_vp[1]}\n  Player 2: {engine.game_state.total_vp[2]}"
    )
    if engine.game_state.total_vp[1] > engine.game_state.total_vp[2]:
        print(">> Player 1 wins!")
    elif engine.game_state.total_vp[2] > engine.game_state.total_vp[1]:
        print(">> Player 2 wins!")
    else:
        print(">> It's a tie!")


if __name__ == "__main__":
    main()
