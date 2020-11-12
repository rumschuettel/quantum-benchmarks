from typing import Dict
from pathlib import Path

import numpy as np
from math import pi
from numpy import arccos, sqrt
import random as random
from pylab import rcParams
from matplotlib import pyplot as plt

from libbench import VendorJob

from .matrices import MATRICES


class HHLBenchmarkMixin:
    def __init__(
        self,
        matrix,
        num_shots,
        shots_multiplier,
        **_,
    ):
        super().__init__()

        self.matrix = MATRICES[matrix]
        self.num_shots = num_shots
        self.shots_multiplier = shots_multiplier

    def collate_results(self, results: Dict[VendorJob, object]):

        # output arrays
        histograms = np.zeros((2 ** self.num_qubits, 2 ** self.num_qubits), dtype=np.float64)

        # fill in with values from jobs
        for job in results:
            result = results[job]
            basis_vec = result["basis_vec"]
            histogram = result["histogram"]
            total = 0
            for i in range(0, 2 ** self.num_qubits):
                total += histogram[i]
            for i in range(0, 2 ** self.num_qubits):
                # histograms[i][basis_vec]+=histogram[i]/(self.num_shots*self.shots_multiplier)
                histograms[i][basis_vec] += histogram[i] / total

        # Print histogram for debugging purposes
        print(histograms)

        return histograms

    def visualize(self, collated_result: object, path: Path) -> Path:
        # Unpack the collated result
        histograms = collated_result
        extent = (0, 2 ** self.num_qubits, 0, 2 ** self.num_qubits)

        # Set up the figure
        fig, ax = plt.subplots(nrows=1, ncols=1)  # create figure & 1 axis

        # Draw the postselection probabilities
        ax.imshow(histograms, cmap="gray", extent=extent, vmin=0, vmax=1)
        # ax.imshow(histograms, cmap="nipy_spectral", extent=extent, vmin=0, vmax=1)
        ax.set_title(f"HHL({self.num_qubits})")
        ax.set_xlabel("Input state")
        ax.set_ylabel("Histogram")

        # save figure
        figpath = path / "visualize.pdf"
        fig.savefig(figpath)

        # default figure to display
        return figpath

    def __repr__(self):
        return str(
            {
                "block_encoding": self.block_encoding,
                "num_qubits": self.num_qubits,
                "num_ancillas": self.num_ancillas,
                "qsvt_poly": self.qsvt_poly,
                "num_shots": self.num_shots,
                "shots_multiplier": self.shots_multiplier,
            }
        )


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser("HHL", help="HHL QSVT benchmark.", **argparse_options)
    parser.add_argument(
        "-b",
        "--matrix",
        type=str,
        help=f"one of the precomputed matrices {', '.join(MATRICES.keys())}",
        default=list(MATRICES.keys())[0],
    )
    parser.add_argument(
        "-s",
        "--num_shots",
        type=int,
        help="Number of shots per orientation",
        default=8096,
    )
    parser.add_argument(
        "-m",
        "--shots_multiplier",
        type=int,
        help="Multiplier for shots per orientation",
        default=1,
    )
    return parser
