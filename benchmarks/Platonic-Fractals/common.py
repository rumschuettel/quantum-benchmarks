from typing import Dict, Tuple
from pathlib import Path

import numpy as np
from math import pi
from numpy import arccos, sqrt
import random as random
from pylab import rcParams
from matplotlib import pyplot as plt
import matplotlib
import pandas as pd

from libbench import VendorJob
import itertools


class PlatonicFractalsBenchmarkMixin:
    BODY_OCTA = 0

    def __init__(self, body, strength, num_steps, num_shots, shots_multiplier, **_):
        super().__init__()

        self.body = body
        self.strength = strength
        self.num_steps = num_steps
        self.num_shots = num_shots
        self.shots_multiplier = shots_multiplier

    def collate_results(self, results: Dict[VendorJob, object], threshold=1):
        dirStats = {}

        # fill in with values from jobs
        for result in results.values():
            dirs = tuple(result["dirs"])
            if not dirs in dirStats:
                dirStats[dirs] = result
            if "ymeascounts" in result:
                if not "ymeascounts" in dirStats[dirs]:
                    dirStats[dirs].update(result)
                else:
                    for meas in result["ymeascounts"]:
                        if meas not in dirStats[dirs]["ymeascounts"]:
                            dirStats[dirs]["ymeascounts"][meas] = result["ymeascounts"][meas]
                            dirStats[dirs]["ystates"][meas] = result["ystates"][meas]
                        else:
                            total = (
                                result["ymeascounts"][meas] + dirStats[dirs]["ymeascounts"][meas]
                            )
                            dirStats[dirs]["ystates"][meas] = (
                                result["ymeascounts"][meas] * result["ystates"][meas]
                                + dirStats[dirs]["ymeascounts"][meas]
                                * dirStats[dirs]["ystates"][meas]
                            ) / total
                            dirStats[dirs]["ymeascounts"][meas] = total
            elif "zmeascounts" in result:
                if not "zmeascounts" in dirStats[dirs]:
                    dirStats[dirs].update(result)
                else:
                    for meas in result["zmeascounts"]:
                        if meas not in dirStats[dirs]["zmeascounts"]:
                            dirStats[dirs]["zmeascounts"][meas] = result["zmeascounts"][meas]
                            dirStats[dirs]["zstates"][meas] = result["zstates"][meas]
                        else:
                            total = (
                                result["zmeascounts"][meas] + dirStats[dirs]["zmeascounts"][meas]
                            )
                            dirStats[dirs]["zstates"][meas] = (
                                result["zmeascounts"][meas] * result["zstates"][meas]
                                + dirStats[dirs]["zmeascounts"][meas]
                                * dirStats[dirs]["zstates"][meas]
                            ) / total
                            dirStats[dirs]["zmeascounts"][meas] = total

        points = {}

        for dirs in dirStats:
            if "ymeascounts" in dirStats[dirs] and "zmeascounts" in dirStats[dirs]:
                for meas in dirStats[dirs]["ymeascounts"]:
                    if meas in dirStats[dirs]["zmeascounts"]:
                        if (
                            dirStats[dirs]["ymeascounts"][meas] > threshold
                            and dirStats[dirs]["zmeascounts"][meas] > threshold
                        ):
                            points[(dirs, meas)] = (
                                dirStats[dirs]["ystates"][meas],
                                dirStats[dirs]["zstates"][meas],
                            )

        return points

    def visualize(self, collated_result: object, path: Path) -> Path:
        # def visualize(self, points, figName):
        rcParams["figure.figsize"] = 7, 7

        points = collated_result.values()

        theta = np.arange(0, 2 * np.pi, 0.004)

        fig, ax = plt.subplots(nrows=1, ncols=1)  # create figure 1
        plt.plot(1 * np.cos(theta), 1 * np.sin(theta), color="#14498C")
        plt.scatter(*zip(*points), color="#A3E3D9")
        ax.set_facecolor("black")
        ax.set_xlim([-1.1, 1.1])
        ax.set_ylim([-1.1, 1.1])

        figpath = path / "visualize.pdf"
        fig.savefig(figpath)  # save the figure to file

        pts_by_path = (
            pd.DataFrame(
                {tuple(zip(dirs, meas)): pt for ((dirs, meas), pt) in collated_result.items()}
            )
            .sort_index(axis=1)
            .T
        )

        lines = []
        widths = []
        colors = []

        def _iter_level(df: pd.DataFrame, level: int = 0) -> np.array:
            mean = df.mean().to_numpy()
            if len(df) > 1:
                for _, ddff in df.groupby(level=-level - 1):
                    mean2 = _iter_level(ddff, level + 1)
                    STEP = 0.2
                    for x in np.arange(0, 1, STEP):
                        pt_a = (1 - x) * mean + x * mean2
                        pt_b = (1 - (x + STEP)) * mean + (x + STEP) * mean2
                        lines.append([tuple(pt_a), tuple(pt_b)])
                        widths.append(10 / (x + level + 1))
                        colors.append(1 / (x + level + 1))
            return mean

        _iter_level(pts_by_path)
        lines.reverse(), widths.reverse(), colors.reverse()

        lc = matplotlib.collections.LineCollection(
            lines,
            linewidths=widths,
            cmap=plt.get_cmap("inferno"),
            norm=plt.Normalize(vmin=-0.1, vmax=1.5),
            capstyle="round",
        )
        lc.set_array(np.array(colors))

        fig, ax = plt.subplots(nrows=1, ncols=1)  # create figure 2
        ax.add_collection(lc)
        ax.scatter(*zip(*points), color="#000000")
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        plt.margins(0, 0)
        plt.axis("off")
        figpath = path / "visualize2.pdf"
        fig.savefig(
            figpath, transparent=True, bbox_inches="tight", pad_inches=0
        )  # save the figure to file

        # default figure to display
        return figpath

    def _reference_for_point(self, directions: tuple, outcomes: str) -> np.array:
        """
        for a tuple of directions and outcomes like ((3, 1), '01'), calculate
        where that point lies in the plot; i.e. in this case, go in +3 direction,
        then in -1 direction, where the strength attenuates by self.strength
        """
        DIRS_LUT = {
            (1, "0"): -np.array([0.0, 0.0, 1.0]),
            (2, "0"): np.array([1.0, 0.0, 0.0]),
            (3, "0"): np.array([0.0, 1.0, 0.0]),
            (1, "1"): np.array([0.0, 0.0, 1.0]),
            (2, "1"): -np.array([1.0, 0.0, 0.0]),
            (3, "1"): -np.array([0.0, 1.0, 0.0]),
        }
        # TODO: double check that this formula is indeed correct
        k = (1 - np.sqrt(1 - self.strength ** 2)) / self.strength
        r = -np.array([0.0, 0.0, 1.0])
        for step in zip(directions, outcomes):
            n = k * DIRS_LUT[step]
            r = ((1 - k ** 2) * r + 2 * (1 + n @ r) * n) / (1 + k ** 2 + 2 * n @ r)
        return r[:2]

    def score(self, collated_result: object, *_):
        distances = []

        # for each point, add distance to reference point
        for key, point in collated_result.items():
            distances.append(
                np.linalg.norm(np.array(point) - self._reference_for_point(*key), ord=2)
            )

        # from this extract overall mean and standard deviation of this mean
        mean = np.mean(distances, axis=0)
        stddev_mean = np.std(distances, axis=0)

        print(self.num_steps, "steps")
        print(f"avg l2 distance: {mean:.3f}±{stddev_mean:.3f}")

    def __repr__(self):
        return str(
            {
                "body": self.body,
                "strength": self.strength,
                "num_steps": self.num_steps,
                "num_shots": self.num_shots,
                "shots_multiplier": self.shots_multiplier,
            }
        )


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser(
        "Platonic-Fractals", help="Platonic Fractals benchmark.", **argparse_options
    )
    parser.add_argument(
        "-b", "--body", type=int, help="The type of the Platonic body; (0 -- Octahedron)", default=0
    )
    parser.add_argument(
        "-e", "--strength", type=float, help="The strength of the mesurements", default=0.93
    )
    parser.add_argument("-t", "--num_steps", type=int, help="Depth of fractal", default=2)
    parser.add_argument(
        "-s", "--num_shots", type=int, help="Number of shots per orientation", default=1024
    )
    parser.add_argument(
        "-m",
        "--shots_multiplier",
        type=int,
        help="Multiplier for shots per orientation",
        default=10,
    )
    return parser
