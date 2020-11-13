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

        used_qubits = (self.matrix["qubits"]-self.matrix["ancillas"])

        # output arrays
        histograms = np.zeros((2 ** used_qubits, 2 ** used_qubits), dtype=np.float64)

        # fill in with values from jobs
        for job in results:
            result = results[job]
            basis_vec = result["basis_vec"]
            histogram = result["histogram"]
            total = 0
            for i in range(2 ** used_qubits):
                total += histogram[i]
            for i in range(2 ** used_qubits):
                # histograms[i][basis_vec]+=histogram[i]/(self.num_shots*self.shots_multiplier)
                histograms[i][basis_vec] += histogram[i] / total

        # Print histogram for debugging purposes
        print(histograms)

        return histograms

    def visualize(self, collated_result: object, path: Path) -> Path:
        # Unpack the collated result
        used_qubits = (self.matrix["qubits"]-self.matrix["ancillas"])        
        #histograms = np.flip(collated_result,0)     
        histograms = collated_result
        #extent = (0, 2 ** used_qubits, 2 ** used_qubits, 0)

        # Set up the figure
        fig, ax = plt.subplots(nrows=1, ncols=1)  # create figure & 1 axis

        # Draw the measurement probabilities
        ax.imshow(histograms, cmap="gray", vmin=0, vmax=1, origin='lower')
        # ax.imshow(histograms, cmap="nipy_spectral", extent=extent, vmin=0, vmax=1)
        ax.set_title(f"HHL({used_qubits})")
        ax.set_xlabel("Input state")
        ax.set_xticks(range(2 ** used_qubits))
        ax.set_xticklabels(range(2 ** used_qubits))
        ax.set_ylabel("Histogram")
        ax.set_yticks(range(2 ** used_qubits))
        ax.set_yticklabels(reversed(range(2 ** used_qubits)))    

        # save figure
        figpath = path / "visualize.pdf"
        fig.savefig(figpath)

        # default figure to display
        return figpath

    def __repr__(self):
        return str(
            {
                "matrix": self.matrix,
                "num_shots": self.num_shots,
                "shots_multiplier": self.shots_multiplier,
            }
        )


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser("HHL", help="HHL QSVT benchmark.", **argparse_options)
    parser.add_argument(
        "-c",
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
