import math

DIRECTION_VECTORS = {
    "N": (0, -1), "NNE": (0.38, -0.92), "NE": (0.71, -0.71), "ENE": (0.92, -0.38),
    "E": (1, 0), "ESE": (0.92, 0.38), "SE": (0.71, 0.71), "SSE": (0.38, 0.92),
    "S": (0, 1), "SSW": (-0.38, 0.92), "SW": (-0.71, 0.71), "WSW": (-0.92, 0.38),
    "W": (-1, 0), "WNW": (-0.92, -0.38), "NW": (-0.71, -0.71), "NNW": (-0.38, -0.92)
}

RECTANGLE_WALL = [(i, j) for i in range(6) for j in range(2)]  # 3"x1" = 6x2 tiles
L_SHAPE_WALL = [(0, i) for i in range(12)] + [(1, 11), (2, 11)]  # 6" tall + 2" base

def rotate_shape(shape, direction):
    dx, dy = DIRECTION_VECTORS[direction.upper()]
    return [(
        round(x * dx - y * dy),
        round(x * dy + y * dx)
    ) for x, y in shape]

def generate_spiral_offsets(radius=4):
    spiral = [(0, 0)]
    for layer in range(1, radius + 1):
        for dx in range(-layer, layer + 1):
            for dy in range(-layer, layer + 1):
                if abs(dx) == layer or abs(dy) == layer:
                    spiral.append((dx, dy))
    return spiral
