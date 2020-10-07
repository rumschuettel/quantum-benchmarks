from typing import Dict
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from libbench import VendorJob, print_hl


class SchroedingerMicroscopeBenchmarkMixin:
    def __init__(self, num_post_selections, num_pixels, num_shots, xmin, xmax, ymin, ymax, **_):
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

    def visualize(self, collated_result: object, path: Path) -> Path:
        # Unpack the collated result
        zs, psps = collated_result
        extent = (self.xmin, self.xmax, self.ymin, self.ymax)

        # Set up the figure
        fig = plt.figure(figsize=(12, 8))
        ax_psps = fig.add_subplot(1, 2, 1)
        ax_sps = fig.add_subplot(1, 2, 2)

        # Draw the postselection probabilities
        ax_psps.imshow(
            psps ** (1 / (2 ** self.num_post_selections - 1)),
            cmap="gray",
            extent=extent,
            vmin=0,
            vmax=1,
        )
        ax_psps.set_title(f"PSP({self.num_post_selections},{self.num_pixels},{self.num_shots})")
        ax_psps.set_xlabel("Re(z)")
        ax_psps.set_ylabel("Im(z)")

        # Draw the success probabilities
        ax_sps.imshow(zs, cmap="gray", extent=extent, vmin=0, vmax=1)
        ax_sps.set_title(f"SP({self.num_post_selections},{self.num_pixels},{self.num_shots})")
        ax_sps.set_xlabel("Re(z)")
        ax_sps.set_ylabel("Im(z)")

        # save figure
        figpath = path / "visualize.pdf"
        fig.savefig(figpath)

        # Set up the figure
        fig = plt.figure(figsize=(4.2,2))
        fig.subplots_adjust(left = 0, right = 1, bottom = 0, top = 1, hspace = 0, wspace = 0)
        ax_psps = fig.add_subplot(1, 2, 1)
        ax_sps = fig.add_subplot(1, 2, 2)

        # Draw the postselection probabilities
        ax_psps.imshow(
            psps ** (1 / (2 ** self.num_post_selections - 1)),
            cmap="gray",
            extent=extent,
            vmin=0,
            vmax=1,
        )
        ax_psps.set_xticks([])
        ax_psps.set_yticks([])

        # Draw the success probabilities
        ax_sps.imshow(zs, cmap="gray", extent=extent, vmin=0, vmax=1)
        ax_sps.set_xticks([])
        ax_sps.set_yticks([])

        # save the figure for the overview page
        devfigpath = path / "visualize-devpage.pdf"
        fig.savefig(devfigpath)

        # default figure to display
        return figpath

    def __repr__(self):
        return str(
            {
                "num_post_selections": self.num_post_selections,
                "num_pixels": self.num_pixels,
                "num_shots": self.num_shots,
            }
        )


def score(benchmark_data: object, reference_data: object):
    zs, _ = benchmark_data
    zs_ref, _ = reference_data

    mse = ((zs - zs_ref) ** 2).mean(axis=None)
    print_hl("MSE", color="white", end=" ")
    print_hl(mse, color="red")


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser(
        "Schroedinger-Microscope", help="Schroedinger microscope benchmark.", **argparse_options
    )
    parser.add_argument(
        "-ps", "--num_post_selections", type=int, help="Number of post selections rounds", default=1
    )
    parser.add_argument("-p", "--num_pixels", type=int, help="Number of pixels", default=4)
    parser.add_argument(
        "-s", "--num_shots", type=int, help="Number of shots per pixel", default=1024
    )
    parser.add_argument("--xmin", type=float, help="Minimal x-value", default=-2)
    parser.add_argument("--xmax", type=float, help="Maximal x-value", default=2)
    parser.add_argument("--ymin", type=float, help="Minimal y-value", default=-2)
    parser.add_argument("--ymax", type=float, help="Maximal y-value", default=2)
    return parser
