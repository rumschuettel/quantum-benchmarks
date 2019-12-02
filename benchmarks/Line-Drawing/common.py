from typing import Dict
from pathlib import Path
import os

import numpy as np
import itertools as it

np.set_printoptions(linewidth=200)
import matplotlib.pyplot as plt
import itertools as it

from libbench import VendorJob, is_power_of_2
from .shapes import SHAPE_FUNCTIONS


class LineDrawingBenchmarkMixin:
    def __init__(self, shape, state_preparation_method, tomography_method, num_points, num_shots, num_repetitions, **_):
        super().__init__()
        assert is_power_of_2(num_points), "number of points needs to be power of 2"
        assert shape in SHAPE_FUNCTIONS, f"{shape} not one of {SHAPE_FUNCTIONS.keys()}"

        points = [
            complex(*SHAPE_FUNCTIONS[shape](t))
            for t in np.linspace(0, 2 * np.pi, num=num_points + 1)[:num_points]
        ]
        self.points = np.array(points) / np.linalg.norm(points)

        self.state_preparation_method = state_preparation_method
        self.tomography_method = tomography_method
        self.num_shots = num_shots
        self.num_repetitions = num_repetitions
        self.shape = shape

        # correction angle as reference to re-orient final drawing
        self.correction_angle = np.angle(points[0])

    def collate_results(self, results: Dict[VendorJob, object], path: Path):
        n = int(np.log2(len(self.points)))

        # Retrieve the amplitude estimates
        curves = []
        for j in range(self.num_repetitions):
            prob_hists = {}
            for pauli_string in it.product(['X','Y','Z'], repeat = n):
                if self.tomography_method == "custom" and pauli_string.count('Z') < n-1: continue

                # Retrieve the measurement statistics
                for job in results:
                    if job.repetition == j and job.pauli_string == pauli_string:
                        prob_hists[''.join(pauli_string)] = results[job]
                        break
                else:
                    raise AssertionError(f"The probability job with repetition {j} was not found in the results data structure.")

            if self.tomography_method == "custom":
                estimates = {k : np.sqrt(v) for k,v in prob_hists['Z'*n].items()}
                for k in range(n - 1, -1, -1):
                    cos_hist = prob_hists['Z'*k + 'X' + 'Z'*(n-k-1)]
                    sin_hist = prob_hists['Z'*k + 'Y' + 'Z'*(n-k-1)]

                    its = [["0"]] * (k + 1) + [["0", "1"]] * (n - 1 - k)
                    for j0 in it.product(*its):
                        j0 = "".join(j0)
                        j1 = j0[:k] + "1" + j0[(k + 1) :]
                        fact = abs(estimates[j0] * estimates[j1])
                        if fact == 0:
                            continue
                        cos_phase_diff = (cos_hist[j0] - cos_hist[j1]) / (2 * fact)
                        sin_phase_diff = (sin_hist[j0] - sin_hist[j1]) / (2 * fact)
                        phase_diff = np.arctan2(sin_phase_diff, cos_phase_diff)

                        # Iterate over the part of the Hamming cube that is influenced
                        new_its = [["0", "1"]] * k + [["1"]] + [[j0[i]] for i in range(k + 1, n)]
                        for j1 in it.product(*new_its):
                            j1 = "".join(j1)
                            estimates[j1] *= np.exp(-1.0j * phase_diff)

                curve = np.array([v for k, v in sorted(estimates.items())])

            else: #self.tomography_method == "GKKT"

                # eigenstates of the paulis
                eigenstates = {
                    'X0' : np.array([1,1], dtype = np.complex64) / np.sqrt(2),
                    'X1' : np.array([1,-1], dtype = np.complex64) / np.sqrt(2),
                    'Y0' : np.array([1,1.j], dtype = np.complex64) / np.sqrt(2),
                    'Y1' : np.array([1,-1.j], dtype = np.complex64) / np.sqrt(2),
                    'Z0' : np.array([1,0], dtype = np.complex64),
                    'Z1' : np.array([0,1], dtype = np.complex64)
                }

                approx = np.zeros((2**n, 2**n), dtype = np.complex64)
                for pauli_string in it.product(['X', 'Y', 'Z'], repeat=n):
                    for o,f in prob_hists[''.join(pauli_string)].items():
                        m = np.array([1], dtype = np.complex64)
                        for pi,oi in zip(pauli_string, o):
                            basis_state = eigenstates[pi+oi]
                            tensor = np.conj(basis_state.T)[np.newaxis,:] * basis_state[:,np.newaxis] - np.eye(2) / 3
                            m = np.kron(m, tensor)
                        m *= f
                        approx += m / (3**n)

                # Obtain the largest eigenvector
                w,v = np.linalg.eigh(approx)
                idx = w.argsort()[::-1]
                w = w[idx]
                v = v[:,idx]
                curve = v[:,0] / np.exp(1.j * np.angle(v[0,0]))

            corrected_curve = curve * np.exp(1.j * self.correction_angle)
            curves.append(corrected_curve)
        return curves

    def visualize(self, collated_result: object, path: Path) -> Path:
        # Set up the figure
        fig = plt.figure(figsize=(8, 8))
        ax = fig.gca()

        # Plot the contours
        for curve in collated_result:
            xs, ys = list(np.real(curve)), list(np.imag(curve))
            # print("X coordinates:", np.round(xs,3))
            # print("Y coordinates:", np.round(ys,3))
            ax.plot(xs + [xs[0]], ys + [ys[0]], color="black", alpha=0.3)

        # Plot an averaged contour
        from matplotlib.collections import LineCollection

        def interp(a, fac=100):
            return np.interp(
                np.linspace(0, len(a) - 1 / fac, fac * len(a)), range(len(a)), a, period=len(a)
            )

        all = np.array(collated_result)
        avg = np.mean(all, axis=0)
        avg_x, avg_y = interp(np.real(avg)), interp(np.imag(avg))
        avg_pts = np.array([avg_x, avg_y]).T.reshape(-1, 1, 2)
        widths = interp(
            (np.std(np.real(all), axis=0) ** 2 + np.std(np.imag(all), axis=0) ** 2) ** (1 / 2)
        )
        axes_scale = np.linalg.norm(ax.transData.transform([1, 0]) - ax.transData.transform([0, 0]))
        widths *= 72.0 * axes_scale / fig.dpi
        avg_segments = np.concatenate([avg_pts[:-1], avg_pts[1:]], axis=1)
        ax.add_collection(
            LineCollection(avg_segments, linewidths=widths, color="red", capstyle="round")
        )

        # Plot the ideal contour
        ideal_xs, ideal_ys = list(np.real(self.points)), list(np.imag(self.points))
        ax.plot(ideal_xs + [ideal_xs[0]], ideal_ys + [ideal_ys[0]], color="yellow", linestyle="--")

        xmin, xmax, ymin, ymax = (min(ideal_xs), max(ideal_xs), min(ideal_ys), max(ideal_ys))
        dx, dy = xmax - xmin, ymax - ymin
        if dx < dy * 1.5:
            dx = dy * 1.5
        else:
            dy = dx / 1.5

        ax.set_xlim((xmin - 0.1 * dx, xmax + 0.1 * dx))
        ax.set_ylim((ymin - 0.1 * dy, ymax + 0.1 * dy))

        # save figure
        figpath = path / "visualize.pdf"
        fig.savefig(figpath)

        # default figure to display
        return figpath

    def __repr__(self):
        return str(
            {
                "shape": self.shape,
                "num_points": len(self.points),
                "num_repetitions": self.num_repetitions,
                "state_preparation_method": self.state_preparation_method,
                "tomography_method": self.tomography_method
            }
        )


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser("Line-Drawing", help="Line drawing benchmark.", **argparse_options)
    parser.add_argument(
        "--shape",
        type=str,
        help=f"The shape to draw, one of {SHAPE_FUNCTIONS.keys()}",
        default="heart",
    )
    parser.add_argument("-sm", "--state_preparation_method", type=str, help="State preparation method", default="BVMS")
    parser.add_argument("-tm", "--tomography_method", type=str, help="Tomography method", default="GKKT")
    parser.add_argument(
        "-n",
        "--num_points",
        type=int,
        help="Number of points to draw; has to be a power of 2",
        default=4,
    )
    parser.add_argument(
        "-s", "--num_shots", type=int, help="Number of shots per circuit", default=1024
    )
    parser.add_argument(
        "-r", "--num_repetitions", type=int, help="Number of repetitions", default=1
    )
    return parser
