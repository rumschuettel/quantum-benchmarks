import numpy as np
import matplotlib.pyplot as plt

# The transform
def F(z):
    return (z ** 2 + 1j) / (1j * z ** 2 + 1)


# Iterated transform
def Fcirc(n, z):
    if n == 0:
        return z
    if n == 1:
        return F(z)
    return Fcirc(n - 1, F(z))


# The success probability
def p1(n, z):
    return 1 / (np.abs(Fcirc(n, z)) ** 2 + 1)


# The post selection probability
def pps(n, z):
    f = 1.0
    for j in range(1, n + 1):
        x = Fcirc(n - j, z)
        f *= ((abs(x) ** 4 + 1) / (abs(x) ** 2 + 1) ** 2) ** (2 ** (j - 1))
    return f


# Calculate the pixel values for the pictures
def make_pictures(n, p):
    xs = np.linspace(-2.0, 2.0, p + 1)
    xs = 0.5 * (xs[:-1] + xs[1:])
    zs = xs[np.newaxis, :] + 1j * xs[:, np.newaxis]
    pss = pps(n, zs)
    ss = p1(n, zs)
    return pss, ss
