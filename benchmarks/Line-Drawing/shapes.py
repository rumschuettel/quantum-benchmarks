from numpy import cos, sin

SHAPE_FUNCTIONS = {
    "heart": lambda t: (
        16 * sin(t) ** 3,
        13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t),
    )
}
