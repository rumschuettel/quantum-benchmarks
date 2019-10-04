from typing import Dict

import numpy as np
from math import pi
from numpy import arccos,sqrt
from pylab import rcParams
from matplotlib import pyplot as plt

from libbench import VendorJob



class PlatonicFractalsBenchmarkMixin:
    def __init__(self, body, strength, numPoints, numSteps, numRuns, randomSeed):
        super().__init__()

        self.body = body
        self.strength = strength
        self.numPoints = numPoints
        self.numSteps = numSteps
        self.numRuns = numRuns
        self.randomSeed = randomSeed

    def collate_results(self, results: Dict[VendorJob, object]):
        # get array dimensions right
        xs = np.linspace(self.xmin, self.xmax, self.num_pixels + 1)
        xs = 0.5 * (xs[:-1] + xs[1:])
        ys = np.linspace(self.ymin, self.ymax, self.num_pixels + 1)

        # output arrays
        zs = np.empty((len(xs), len(ys)), dtype=np.float64)
        psps = np.empty((len(xs), len(ys)), dtype=np.float64)

        # fill in with values from jobs
        for job in results:
            result = results[job]

            zs[job.j, job.i] = result["z"]
            psps[job.j, job.i] = result["psp"]

        return zs, psps

<<<<<<< HEAD
    def visualize(self, points, figName):
        rcParams['figure.figsize'] = 7, 7

        theta = np.arange(0, 2*np.pi , 0.004)        

        fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
        plt.plot(1 * np.cos(theta), 1 * np.sin(theta),color='#14498C')#'#A3E3D9'#'#14498C'
        plt.scatter(*zip(*points),color='#A3E3D9')#'#3ACC23'
        ax.set_facecolor('xkcd:black')#'xkcd:salmon'
        ax.set_xlim([-1.1,1.1])
        ax.set_ylim([-1.1,1.1])

        fig.savefig('figName')   # save the figure to file
        plt.close(fig)
=======
def argparser(toadd):
    parser = toadd.add_parser("Platonic-Fractals", help="Platonic Fractals benchmark.")
    return parser
>>>>>>> 9d2d1f1025b47db464dafc9e08f751330d75dbbd
