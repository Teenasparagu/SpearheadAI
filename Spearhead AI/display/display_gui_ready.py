import tkinter as tk

CELL_SIZE = 20  # Size of each square in pixels

class BoardGUI:
    def __init__(self, board):
        self.board = board
        self.root = tk.Tk()
        self.root.title("Spearhead AI Board")
        self.canvas = tk.Canvas(
            self.root,
            width=board.width * CELL_SIZE,
            height=board.height * CELL_SIZE
        )
        self.canvas.pack()
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        for y in range(self.board.height):
            for x in range(self.board.width):
                self.draw_tile(x, y)

    def draw_tile(self, x, y):
        tile = "-"
        for obj in self.board.objectives:
            if obj.x == x and obj.y == y:
                tile = "O"

        for unit in self.board.units:
            for i, model in enumerate(unit.models):
                if model.x == x and model.y == y:
                    tile = "U" if i == 0 else "u"

        color = {
            "-": "white",      # empty
            "O": "yellow",     # objective
            "U": "blue",       # unit leader
            "u": "lightblue",  # other models
            "T": "gray"        # terrain (if added later)
        }.get(tile, "red")     # fallback for undefined tiles

        self.canvas.create_rectangle(
            x * CELL_SIZE, y * CELL_SIZE,
            (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
            fill=color, outline="black"
        )

    def update(self):
        self.draw_board()
        self.root.update_idletasks()
        self.root.update()
