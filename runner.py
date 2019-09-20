#!/usr/bin/env python

import argparse
import glob
import importlib
import os

from libbench import VendorBenchmark, VendorLink, print_hl

i = importlib.import_module("matplotlib.text")

# find runnable test modules and vendors
BENCHMARKS = [
    os.path.basename(folder)
    for folder in glob.glob("./benchmarks/*")
    if os.path.isdir(folder)
]
VENDORS = [
    os.path.basename(folder)
    for folder in glob.glob("./libbench/*")
    if os.path.isdir(folder)
]


def info(link: VendorLink):
    print("available devices:")
    for name in link.get_devices():
        print(name)


def run(benchmark: VendorBenchmark, link: VendorLink, device_name: str):
    results = []

    # run every job and collect outcomes
    for job in benchmark.get_jobs():
        result = job.run(link.get_device(device_name))
        parsed_result = benchmark.parse_result(job, result)
        print(parsed_result)
        results.append(parsed_result)

    # collate all results together
    collated_results = benchmark.collate_results(parsed_result)
    print(collated_results)


def import_benchmark(name, vendor, simulate):
    benchmark_module = importlib.import_module(f"benchmarks.{name}.{vendor}")
    return getattr(benchmark_module, "Benchmark" if not simulate else "SimulatedBenchmark")


def import_link(vendor, simulate):
    vendor_module = importlib.import_module(f"libbench.{vendor}")
    return getattr(vendor_module, "Link" if not simulate else "SimulatorLink")


if __name__ == "__main__":
    print_hl("Quantum Benchmarking Suite", color="cyan")

    # arguments
    parser = argparse.ArgumentParser(description="Quantum Benchmark")
    parser.add_argument(
        "vendor",
        metavar="VENDOR",
        type=str,
        help=f"vendor to use; one of {', '.join(VENDORS)}",
    )
    parser.add_argument("-i", action="store_true", help="show vendor info")
    parser.add_argument("--device", metavar="DEVICE", default="", type=str, help="device to use with chosen vendor; run -i to get a list.")
    parser.add_argument("-s", action="store_true", help="simulate")
    parser.add_argument(
        "--benchmark",
        metavar="BENCHMARK",
        type=str,
        help=f"benchmark to run; one of {', '.join(BENCHMARKS)}",
    )

    args = parser.parse_args()
    print(args)

    VENDOR = args.vendor.lower()
    DEVICE = args.device.lower()
    INFO = args.i
    SIMULATE = args.s
    BENCHMARK = args.benchmark

    assert VENDOR in VENDORS, "vendor does not exist"
    assert BENCHMARK is None or BENCHMARK in BENCHMARKS, "benchmark does not exist"

    # pick backend
    Link = import_link(VENDOR, SIMULATE)
    link = Link()

    # pick command
    if INFO:
        info(link)

    if BENCHMARK:
        # check device exists
        assert DEVICE in link.get_devices(), "device does not exist"


        # edge cases:
        if VENDOR == "ibm" and SIMULATE and DEVICE == "qasm_simulator":
            SIMULATE = False

        Benchmark = import_benchmark(BENCHMARK, VENDOR, SIMULATE)
        run(Benchmark(), link, DEVICE)

    if not INFO and not BENCHMARK:
        parser.print_help()
