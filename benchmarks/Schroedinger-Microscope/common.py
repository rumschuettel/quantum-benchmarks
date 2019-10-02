from typing import Dict

import numpy as np

from libbench import VendorJob


class SchroedingerMicroscopeBenchmarkMixin:
    def __init__(self, num_post_selections, num_pixels, num_shots, xmin, xmax, ymin, ymax):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.num_pixels = num_pixels
        self.num_shots = num_shots
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

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

        return zs, psps


def argparser(toadd):
    parser = toadd.add_parser("Schroedinger-Microscope", help="Schroedinger microscope benchmark.")
    parser.add_argument("-ps", "--num_post_selections", type=int, help="Number of post selections rounds. (default=1)", default=1)
    parser.add_argument("-p", "--num_pixels", type=int, help="Number of pixels. (default=4)", default=4)
    parser.add_argument("-s", "--num_shots", type=int, help="Number of shots per pixel. (default=1024)", default=1024)
    parser.add_argument("--xmin", type=int, help="Minimal x-value (default=-2)", default=-2)
    parser.add_argument("--xmax", type=int, help="Maximal x-value (default=2)", default=2)
    parser.add_argument("--ymin", type=int, help="Minimal y-value (default=-2)", default=-2)
    parser.add_argument("--ymax", type=int, help="Maximal y-value (default=2)", default=2)
    return parser


def paramparser(args):
    return {
        'num_post_selections' : args.num_post_selections,
        'num_pixels' : args.num_pixels,
        'num_shots' : args.num_shots,
        'xmin' : args.xmin,
        'xmax' : args.xmax,
        'ymin' : args.ymin,
        'ymax' : args.ymax
    }
