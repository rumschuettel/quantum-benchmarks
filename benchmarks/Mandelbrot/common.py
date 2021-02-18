from typing import Dict
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from libbench import VendorJob

from .analytics import make_pictures


class MandelbrotBenchmarkMixin:
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
        fig = plt.figure(figsize=(4.2, 2))
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1, hspace=0, wspace=0)
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

    def score(self, collated_result: object, *_):
        zs, psps = collated_result
        Epsps, Ezs = make_pictures(self.num_post_selections, self.num_pixels)

        # Calculate the post-selection score
        scaled_psps = (psps ** (1 / (2 ** self.num_post_selections - 1))).flatten()
        scaled_Epsps = (Epsps ** (1 / (2 ** self.num_post_selections - 1))).flatten()
        # psps_error = np.sqrt(np.mean((scaled_psps.flatten() - scaled_Epsps.flatten())**2))
        # psps_sigma = np.sqrt(np.sum((((scaled_psps - scaled_Epsps) / ((2**self.num_post_selections - 1) * scaled_psps ** (2**self.num_post_selections - 2)))**2 * 1.96**2 * (scaled_psps ** (2**self.num_post_selections - 1) * (1 - scaled_psps ** (2**self.num_post_selections - 1))) / self.num_shots).flatten())) / (self.num_pixels**2 * psps_error)

        psps_error = np.sqrt(np.mean(np.square(scaled_psps - scaled_Epsps)))
        upsps = np.sqrt(psps.flatten() * (1 - psps.flatten()) / self.num_shots)
        scaled_upsps = np.maximum(
            np.abs(np.maximum(psps.flatten() - upsps, 0))
            ** (1 / (2 ** self.num_post_selections - 1))
            - scaled_psps,
            np.abs(
                np.minimum(psps.flatten() + upsps, 1) ** (1 / (2 ** self.num_post_selections - 1))
            )
            - scaled_psps,
        )
        psps_sigma = np.sqrt(np.sum(np.square((scaled_psps - scaled_Epsps) * scaled_upsps))) / (
            self.num_pixels ** 2 * psps_error
        )
        # psps_sigma = 1.96 * np.sqrt(
        #     np.sum(
        #         (scaled_psps - scaled_Epsps)**2
        #         * scaled_psps ** (3 - 2**self.num_post_selections) * (1 - scaled_psps ** (2**self.num_post_selections - 1))
        #         / self.num_shots
        #     )
        # ) / (self.num_pixels**2 * psps_error * (2**self.num_post_selections - 1))

        # Check if more than 10% of the pixels did never pass the post-selection round
        zs_corrected = ((psps > 1e-8) * zs).flatten()
        Ezs_corrected = Ezs.flatten()
        uzs = (
            (psps > 1e-8)
            * np.sqrt(zs * (1 - zs) / (self.num_shots * ((psps > 1e-8) * psps + (psps <= 1e-8))))
            + (psps <= 1e-8)
        ).flatten()

        zs_error = np.sqrt(np.mean(np.square(zs_corrected - Ezs_corrected)))
        zs_sigma = np.sqrt(np.sum(np.square((zs_corrected - Ezs_corrected) * uzs))) / (
            self.num_pixels ** 2 * zs_error
        )

        # zs_error = np.sqrt(np.mean((zs.flatten() - Ezs.flatten())**2))
        # zs_sigma = np.sqrt(np.sum(((zs - Ezs)**2 * 1.96**2 * (zs * (1 - zs)) / (self.num_shots * psps)).flatten())) / (self.num_pixels**2 * zs_error)

        print(f"Post-selection probability error: {psps_error:.4f}±{psps_sigma:.4f}.")
        print(f"Success probability error: {zs_error:.4f}±{zs_sigma:.4f}.")

        return (psps_error, psps_sigma), (zs_error, zs_sigma)

    def __repr__(self):
        return str(
            {
                "num_post_selections": self.num_post_selections,
                "num_pixels": self.num_pixels,
                "num_shots": self.num_shots,
            }
        )


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser("Mandelbrot", help="Mandelbrot benchmark.", **argparse_options)
    parser.add_argument(
        "-ps",
        "--num_post_selections",
        type=int,
        help="Number of post selections rounds",
        default=1,
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
