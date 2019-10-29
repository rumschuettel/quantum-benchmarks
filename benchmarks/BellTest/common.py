from typing import Dict
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

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

        self.distance = distance
        self.topology = (
            topology if topology is not None else [(i, i + 1) for i in range(distance)]
        )
        self.num_shots = num_shots

        # create a list of qubits to test
        graph = nx.Graph(self.topology)

        self.qubit_pairs_to_test = []
        for a in graph.nodes:
            dists = nx.single_source_shortest_path_length(graph, a)
            for b in dists:
                if dists[b] >= 1 and dists[b] <= distance:
                    self.qubit_pairs_to_test.append(nx.shortest_path(graph, a, b))

        assert (
            len(self.qubit_pairs_to_test) > 0
        ), f"no qubit pairs to test at distance <= {distance}"

        print(self.qubit_pairs_to_test)

    def collate_results(self, results: Dict[VendorJob, object], path: Path):
        per_qubit = {}

        for job in results:
            qubit_a, qubit_b = job.qubit_a, job.qubit_b

            # accumulate results here
            if not qubit_a in per_qubit:
                per_qubit[qubit_a] = {}
            acc_a = per_qubit[qubit_a]

            if not qubit_b in acc_a:
                acc_a[qubit_b] = {"bell": 0.0}
            acc_a_b = acc_a[qubit_b]

            # accumulate four measurement outcomes
            res = results[job]
            p = (res["eq"] - res["ineq"]) / (res["eq"] + res["ineq"])
            # bell inequality is P(a,c) - P(a,b) - P(b,c)
            acc_a_b["bell"] += p * (1 if job.test_type == BellTestType.AC else -1)

        return per_qubit

    def visualize(self, collated_result: object, path: Path) -> Path:
        G = nx.Graph(self.topology)
        G_layout = nx.spring_layout(G, seed=0)

        cmap = plt.get_cmap("inferno")
        weight_norm = matplotlib.colors.Normalize(vmin=0.0, vmax=1.5)

        for qubit_a in collated_result:
            # get shortest paths to all other qubits
            # this is a dict { q: dist, ... }
            dists = nx.single_source_shortest_path_length(G, qubit_a)

            # starting at the longest path, set edge weights of graph
            sorted_dists = sorted(
                dists.items(), key=operator.itemgetter(1), reverse=True
            )

            edges = {}
            for qubit_b, _ in sorted_dists:
                if not qubit_b in collated_result[qubit_a]:
                    continue

                weight = weight_norm(collated_result[qubit_a][qubit_b]["bell"])

                # color entire path connecting a and b with this weight
                qubit_path = nx.shortest_path(G, qubit_a, qubit_b)
                for x, y in list(zip(qubit_path[:-1], qubit_path[1:])):
                    edges[(x, y)] = weight
                    edges[(y, x)] = weight

            for u, v, d in G.edges(data=True):
                if (u, v) in edges:
                    d["weight"] = edges[(u, v)]
                else:
                    d["weight"] = 0

            edges, weights = zip(*nx.get_edge_attributes(G, "weight").items())

            nx.draw(
                G,
                G_layout,
                width=10.0,
                node_color=["r" if v == qubit_a else "b" for v in G.nodes()],
                with_labels=True,
                edgelist=edges,
                edge_color=weights,
                edge_cmap=cmap,
                edge_vmin=0,  # we scale the colormap ourselves
                edge_vmax=1,
            )

            print(qubit_a, edges, weights)

            # save figure
            figpath = path / f"visualize-{qubit_a}.pdf"
            plt.savefig(figpath)
            plt.close()

        return None

    def parameter_dict(self):
        return {'distance' : self.distance, 'num_pixels' : self.topology, 'num_shots' : self.num_shots}


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser(
        "BellTest", help="CHSH/Bell Test benchmark.", **argparse_options
    )
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
