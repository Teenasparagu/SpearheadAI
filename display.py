def print_board(board, p1_zone=None, p2_zone=None):
    board_repr = [["-" for _ in range(board.width)] for _ in range(board.height)]

    # Draw deployment zones first
    if p1_zone:
        for x, y in p1_zone:
            if 0 <= x < board.width and 0 <= y < board.height and board_repr[y][x] == "-":
                board_repr[y][x] = "D"
    if p2_zone:
        for x, y in p2_zone:
            if 0 <= x < board.width and 0 <= y < board.height and board_repr[y][x] == "-":
                board_repr[y][x] = "d"

    # Draw terrain next
    for x, y in board.terrain:
        if 0 <= x < board.width and 0 <= y < board.height:
            board_repr[y][x] = "T"

    # Draw objectives
    for obj in board.objectives:
        if 0 <= obj.x < board.width and 0 <= obj.y < board.height:
            board_repr[obj.y][obj.x] = "O"

    # Draw units last (they take priority)
    for unit in board.units:
        for i, model in enumerate(unit.models):
            x, y = model.x, model.y
            if 0 <= x < board.width and 0 <= y < board.height:
                board_repr[y][x] = "U" if i == 0 else "u"

    # Display legend
    print("\nLegend: U = Unit Leader, u = Unit Model, O = Objective, T = Terrain, D = Player 1 Zone, d = Player 2 Zone\n")

    # Display grid
    header = "   " + " ".join(f"{x:2}" for x in range(board.width))
    print(header)
    for y in range(board.height):
        row = " ".join(f"{cell:2}" for cell in board_repr[y])
        print(f"{y:2} {row}")
