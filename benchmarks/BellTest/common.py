from typing import Dict
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import pandas as pd
import networkx as nx
import operator

from libbench import VendorJob

from enum import Enum


class BellTestType(Enum):
    AB = (0, np.pi / 3)
    AC = (0, 2 * np.pi / 3)
    BC = (np.pi / 3, 2 * np.pi / 3)


class BellTestBenchmarkMixin:
    def __init__(self, distance, topology, num_shots, **_):
        super().__init__()

        assert distance > 0, "cannot test bell violation with distance 0"
        if distance == float("inf"):
            assert topology is not None, "specify a distance explicitly when no topology is given"

        self.distance = distance
        self.topology = topology if topology is not None else [(i, i + 1) for i in range(distance)]
        self.num_shots = num_shots

        # create a list of qubits to test
        if self.topology is not None:
            graph = nx.Graph(self.topology)
        else:
            graph = nx.complete_graph(self.distance)

        self.qubit_pairs_to_test = []
        for a in graph.nodes:
            dists = nx.single_source_shortest_path_length(graph, a)
            for b in dists:
                if dists[b] >= 1 and dists[b] <= distance:
                    self.qubit_pairs_to_test.append(nx.shortest_path(graph, a, b))

        assert (
            len(self.qubit_pairs_to_test) > 0
        ), f"no qubit pairs to test at distance <= {distance}"

        print("testing qubit pairs:")
        for p in self.qubit_pairs_to_test:
            print(p)

    def collate_results(self, results: Dict[VendorJob, object], path: Path):
        per_qubit_bell = {}

        for job in results:
            qubit_a, qubit_b = job.qubit_a, job.qubit_b

            # accumulate results here
            if not qubit_a in per_qubit_bell:
                per_qubit_bell[qubit_a] = {}
            acc_a = per_qubit_bell[qubit_a]

            if not qubit_b in acc_a:
                acc_a[qubit_b] = 0.0

            # accumulate four measurement outcomes
            res = results[job]
            p = (res["eq"] - res["ineq"]) / (res["eq"] + res["ineq"])
            # bell inequality is P(a,c) - P(a,b) - P(b,c)
            acc_a[qubit_b] += p * (1 if job.test_type == BellTestType.AC else -1)

        return {"bell": per_qubit_bell}

    def visualize(self, collated_result: object, path: Path) -> Path:
        data = pd.DataFrame(collated_result["bell"])
        data = data.sort_index(axis=0).sort_index(axis=1)
        fig = plt.figure(figsize=(12, 8))
        plt.title(f"Expected Bell Violation ± {1/np.sqrt(self.num_shots):.2f}", y=1.05, size=15)

        # combine them and build a new colormap
        colors1 = matplotlib.cm.get_cmap("Greys")(np.linspace(0.2, 0.8, 200))
        colors2 = matplotlib.cm.get_cmap("inferno")(np.linspace(0.8, 0.2, 100))

        colors = np.vstack((colors1, colors2))
        mymap = mcolors.LinearSegmentedColormap.from_list("bell_map", colors)

        ax = sns.heatmap(
            data,
            cmap=mymap,
            linewidths=0.5,
            vmin=0,
            vmax=1.5,
            square=True,
            linecolor="white",
            annot=True,
            fmt=".2f",
        )
        bottom, top = ax.get_ylim()  # fixes a bug in matplotlib 3.11
        ax.set_ylim(bottom + 0.5, top - 0.5)

        # save figure
        figpath = path / "visualize.pdf"
        fig.savefig(figpath)

        return figpath

    def __repr__(self):
        return str(
            {"distance": self.distance, "topology": self.topology, "num_shots": self.num_shots}
        )


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser("Bell-Test", help="CHSH/Bell Test benchmark.", **argparse_options)
    parser.add_argument(
        "-d",
        "--distance",
        type=int,
        help="Maximum distance between qubits to test; if 0 no restriction",
        default=np.inf,
    )
    parser.add_argument(
        "-s", "--num_shots", type=int, help="Number of shots per test", default=1024
    )
    return parser
