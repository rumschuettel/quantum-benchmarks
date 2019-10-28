from typing import Dict
from pathlib import Path
import os

import numpy as np
np.set_printoptions(linewidth=200)
import matplotlib.pyplot as plt
import itertools as it

from libbench import VendorJob


class LineDrawingBenchmarkMixin:
    def __init__(
        self, filename, method, num_shots, num_repetitions, **_
    ):
        super().__init__()

        points = []
        with open(filename) as f:
            for line in f:
                points.append(complex(line.strip('\n')))

        self.filename = os.path.basename(filename)
        self.points = np.array(points) / np.linalg.norm(points)
        self.state_prepartion_method = method
        self.num_shots = num_shots
        self.num_repetitions = num_repetitions
        for p in self.points:
            if abs(p) > 1e-8:
                self.correction_angle = np.angle(p)
                break
        else:
            raise AssertionError("The points cannot all be located on the origin!")

    def collate_results(self, results: Dict[VendorJob, object], path: Path):

        n = int(np.log2(len(self.points)))
        assert len(self.points) == 2**n

        # Retrieve the amplitude estimates
        curves = []
        for j in range(self.num_repetitions):
            for job in results:
                if job.repetition == j and job.Hadamard_qubit == None and job.S_qubit == None:
                    prob_hist = results[job]
                    estimates = {k : np.sqrt(v) for k,v in prob_hist.items()}
                    break
            else:
                raise AssertionError(f"The probability job with repetition {j} was not found in the results data structure.")

            # Retrieve the relative phase estimates
            for k in range(n-1,-1,-1):
                for job in results:
                    if job.repetition == j and job.Hadamard_qubit == k and job.S_qubit == None:
                        cos_hist = results[job]
                        break
                else:
                    raise AssertionError(f"The job with repetition {j}, Hadamard qubit {k} and S qubit None is missing.")

                for job in results:
                    if job.repetition == j and job.Hadamard_qubit == k and job.S_qubit == k:
                        sin_hist = results[job]
                        break
                else:
                    raise AssertionError(f"The job with repetition {j}, Hadamard qubit {k} and S qubit {k} is missing.")

                its = [['0']]*(k+1) + [['0','1']]*(n-1-k)
                for j0 in it.product(*its):
                    j0 = ''.join(j0)
                    j1 = j0[:k] + '1' + j0[(k+1):]
                    fact = abs(estimates[j0] * estimates[j1])
                    if fact == 0: continue
                    cos_phase_diff = (cos_hist[j0] - cos_hist[j1]) / (2*fact)
                    sin_phase_diff = (sin_hist[j0] - sin_hist[j1]) / (2*fact)
                    phase_diff = np.arctan2(sin_phase_diff, cos_phase_diff)

                    # Iterate over the part of the Hamming cube that is influenced
                    new_its = [['0','1']]*k + [['1']] + [[j0[i]] for i in range(k+1,n)]
                    for j1 in it.product(*new_its):
                        j1 = ''.join(j1)
                        estimates[j1] *= np.exp(-1.j * phase_diff)

            curve = np.array([v for k,v in sorted(estimates.items())]) * np.exp(1.j * self.correction_angle)
            curves.append(curve)
        return curves

    def visualize(self, collated_result: object, path: Path) -> Path:
        # Set up the figure
        fig = plt.figure(figsize=(12, 8))
        ax = fig.gca()

        # Plot the contours
        for curve in collated_result:
            xs,ys = list(np.real(curve)), list(np.imag(curve))
            # print("X coordinates:", np.round(xs,3))
            # print("Y coordinates:", np.round(ys,3))
            ax.plot(xs + [xs[0]], ys + [ys[0]], color = 'red', alpha = .3)

        # Plot the ideal contour
        ideal_xs,ideal_ys = list(np.real(self.points)), list(np.imag(self.points))
        ax.plot(ideal_xs + [ideal_xs[0]], ideal_ys + [ideal_ys[0]], color = 'blue', linestyle = '--')

        xmin,xmax,ymin,ymax = min(ideal_xs),max(ideal_xs),min(ideal_ys),max(ideal_ys)
        dx,dy = xmax-xmin,ymax-ymin
        if dx < dy*1.5: dx = dy*1.5
        else: dy = dx/1.5

        ax.set_xlim((xmin-.1*dx, xmax+.1*dx))
        ax.set_ylim((ymin-.1*dy, ymax+.1*dy))

        # save figure
        figpath = path / "visualize.pdf"
        fig.savefig(figpath)

        # default figure to display
        return figpath


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser(
        "Line-Drawing",
        help="Line drawing benchmark.",
        **argparse_options,
    )
    parser.add_argument(
        "filename",
        type=str,
        help="The file that contains the points to be used."
    )
    parser.add_argument(
        "-m",
        "--method",
        type=str,
        help="State preparation method",
        default="BVMS"
    )
    parser.add_argument(
        "-s", "--num_shots", type=int, help="Number of shots per circuit", default=1024
    )
    parser.add_argument(
        "-r", "--num_repetitions", type=int, help="Number of repetitions", default=1
    )
    return parser
