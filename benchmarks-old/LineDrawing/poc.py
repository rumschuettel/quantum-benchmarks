import numpy as np

np.set_printoptions(linewidth=200)
import matplotlib.pyplot as plt


def convert_zs_to_xs_ys(zs):
    return map(list, zip(*[(np.real(z), np.imag(z)) for z in zs]))


x = 0.35

points = [
    (1, 1),
    (x, 1),
    (0, 1),
    (-x, 1),
    (-1, 1),
    (-1, x),
    (-1, 0),
    (-1, -x),
    (-1, -1),
    (-x, -1),
    (0, -1),
    (x, -1),
    (1, -1),
    (1, -x),
    (1, 0),
    (1, x),
]
n = np.sqrt(sum(x ** 2 + y ** 2 for x, y in points))
points = [(x / n, y / n) for x, y in points]

zs = [x + 1j * y for x, y in points]
amps = np.fft.fft(zs, norm="ortho")
line_zs = [
    sum([a * np.exp(2.0j * np.pi * i * t) for i, a in enumerate(amps)]) / np.sqrt(len(amps))
    for t in np.linspace(0, 1, 200)
]

xs, ys = convert_zs_to_xs_ys(zs)
line_xs, line_ys = convert_zs_to_xs_ys(line_zs)
xs.append(xs[0])
ys.append(ys[0])
line_xs.append(line_xs[0])
line_ys.append(line_ys[0])

fig = plt.figure()
ax = fig.gca()
ax.plot(line_xs, line_ys)
ax.plot(xs, ys, marker=".")
plt.show()
