from typing import Dict

import numpy as np

from libbench import VendorJob


class SchroedingerMicroscopeBenchmarkMixin:
    def __init__(self, num_post_selections, num_pixels, xmin, xmax, ymin, ymax, shots):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.num_pixels = num_pixels
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.shots = shots

    def collate_results(self, results: Dict[VendorJob, object]):
        # get array dimensions right
        xs = np.linspace(self.xmin, self.xmax, self.num_pixels + 1)
        xs = 0.5 * (xs[:-1] + xs[1:])
        ys = np.linspace(self.ymin, self.ymax, self.num_pixels + 1)
        ys = 0.5 * (ys[:-1] + ys[1:])

        # output arrays
        zs = np.empty((len(xs), len(ys)), dtype=np.float64)
        psps = np.empty((len(xs), len(ys)), dtype=np.float64)

        # fill in with values from jobs
        for job in results:
            result = results[job]

            zs[job.j, job.i] = result["z"]
            psps[job.j, job.i] = result["psp"]

        return zs, psps, {
            'num_post_selections' : self.num_post_selections,
            'num_pixels' : self.num_pixels,
            'shots' : self.shots,
            'xmin' : self.xmin,
            'xmax' : self.xmax,
            'ymin' : self.ymin,
            'ymax' : self.ymax
        }
