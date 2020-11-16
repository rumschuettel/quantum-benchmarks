import numpy as np
import matplotlib.pyplot as plt

# The transform
def gen_F(c):
    def F(z):
        return z**2 + c
    return F

# The iterated transform
def gen_Fcirc(c):
    F = gen_F(c)
    def Fcirc(n,z):
        if n == 0: return z
        if n == 1: return F(z)
        return Fcirc(n-1,F(z))
    return Fcirc

# The success probability
def gen_p1(c):
    Fcirc = gen_Fcirc(c)
    def p1(n,z):
        return 1 / (np.abs(Fcirc(n,z))**2 + 1)
    return p1

# The post-selection probability
def gen_pps(c):
    r2 = abs(c) * np.sqrt(.5 * (1 + np.sqrt(1 + 4 / abs(c)**2)))
    r1 = 1/r2
    Fcirc = gen_Fcirc(c)
    def pps(n,z):
        f = 1.
        for j in range(1,n+1):
            x = Fcirc(n-j,z)
            f *= ((abs(x**2 / np.sqrt(1 + r2**2) + np.exp(1.j * np.angle(c)) * r2 / np.sqrt((1 + r1**2) * (1 + r2**2)))**2 + r1**2 / (1 + r1**2)) / (1 + abs(x)**2)**2) ** (2**(j-1))
        return f
    return pps

# Calculate the pixel values for the pictures
def make_pictures(n,p):
    xs = np.linspace(-2., 2., p+1)
    xs = .5 * (xs[:-1] + xs[1:])
    cs = xs[np.newaxis,:] + 1j*xs[:,np.newaxis]

    pss = np.zeros(cs.shape)
    ss = np.zeros(cs.shape)
    for idx,c in np.ndenumerate(cs):
        pss[idx] = gen_pps(c)(n,0)
        ss[idx] = gen_p1(c)(n,0)

    return pss,ss
