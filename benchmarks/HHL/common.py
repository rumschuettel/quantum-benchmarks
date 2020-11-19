from typing import Dict
from pathlib import Path

import numpy as np
from math import pi
from numpy import arccos, sqrt
import random as random
from pylab import rcParams
from matplotlib import pyplot as plt

# For nice printing during debug
from pandas import DataFrame

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
        totals = [0] * 2 ** used_qubits        

        # fill in with values from jobs
        for job in results:
            result = results[job]
            totals[result["basis_vec"]] += result["total"]

        # fill in with values from jobs
        for job in results:
            result = results[job]
            basis_vec = result["basis_vec"]
            histogram = result["histogram"]
            for i in range(2 ** used_qubits):
                # histograms[i][basis_vec]+=histogram[i]/(self.num_shots*self.shots_multiplier)
                histograms[i][basis_vec] += histogram[i] / totals[basis_vec]               

        ideal_stats=self.matrix["histogram"]

        # Print histogram for debugging purposes
        # print(histograms)
        # print(ideal_stats)

        tv=0
        sigma=0
        for i in range(len(histograms)):
            for j in range(len(histograms[0])):
                p=histograms[i][j]*totals[j]/self.num_shots/self.shots_multiplier
                tv += abs(p-ideal_stats[i][j])/2
                sigma += sqrt( p * (1 - p) / (self.num_shots * self.shots_multiplier - 1) )/2

        tv=tv/len(histograms[0])
        print("Average total variation distance: "+str(tv))
        sigma=sigma/len(histograms[0])
        print("Standard deviation: "+str(sigma))        
        
        return histograms

    def visualize(self, collated_result: object, path: Path) -> Path:

        # Unpack the collated result
        used_qubits = (self.matrix["qubits"]-self.matrix["ancillas"])        
    
        histograms = collated_result
        postProbs = np.zeros( 2 ** used_qubits, dtype=np.float64)          
        postHistograms = np.zeros((2 ** used_qubits, 2 ** used_qubits), dtype=np.float64)
      
        for i in range(len(histograms)):
            for j in range(len(histograms[i])): 
                postProbs[j]+=histograms[i][j]

        for j in range(len(histograms)):
            if postProbs[j]==0:
                postProbs[j]=1                

        for i in range(len(histograms)):
            for j in range(len(histograms[i])): 
                postHistograms[i][j]=-histograms[i][j]/postProbs[j]

        min_value=np.min(postHistograms)               

        # Set up the figure
        fig, ax = plt.subplots(nrows=1, ncols=1)  # create figure & 1 axis

        # Draw the measurement probabilities
        # ax.imshow(histograms)          
        ax.imshow(postHistograms, cmap="gray", vmin=min_value, vmax=0)
      
        # Annotate with values for debug purposes
        #for i in range(2 ** used_qubits):
        #    for j in range(2 ** used_qubits):
        #        ax.text(j, i, str(round(histograms[i, j], 4)), ha="center", va="center", color="r")   

        # ax.imshow(histograms, cmap="nipy_spectral", extent=extent, vmin=0, vmax=1)
        ax.set_title(f"HHL(2^{used_qubits})")
        ax.set_xlabel("Input state")
        ax.set_xticks(range(2 ** used_qubits))
        ax.set_xticklabels(range(2 ** used_qubits))
        ax.set_ylabel("Histogram")
        ax.set_yticks(range(2 ** used_qubits))
        ax.set_yticklabels(range(2 ** used_qubits))    

        # save figure
        figpath = path / "visualize.pdf"
        fig.savefig(figpath)

        # default figure to display
        return figpath

    def __repr__(self):
        return str(
            {
                "matrix": { key: self.matrix[key] for key in {"qubits", "ancillas"} },
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
        default=8192,
    )
    parser.add_argument(
        "-m",
        "--shots_multiplier",
        type=int,
        help="Multiplier for shots",
        default=1,
    )
    return parser
