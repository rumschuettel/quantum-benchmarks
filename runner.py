#!/usr/bin/env python

from libbench import print_hl, VendorLink, VendorBenchmark

import argparse
import glob
import importlib
import os

i = importlib.import_module("matplotlib.text")

# find runnable test modules and vendors
BENCHMARKS = [ os.path.basename(folder) for folder in glob.glob("./benchmarks/*") if os.path.isdir(folder) ]
VENDORS = [ os.path.basename(folder) for folder in glob.glob("./libbench/*") if os.path.isdir(folder) ]


def info(link: VendorLink):
    print("available backends:")
    for device in link.get_devices():
        print(device)


def run(benchmark: VendorBenchmark, link: VendorLink):
    for job in benchmark.get_jobs():
        job.run()


def import_benchmark(name, vendor):
    benchmark_module = importlib.import_module(f"benchmark.{name}")
    return getattr(benchmark_module, vendor)

def import_link(vendor, simulate):
    vendor_module = importlib.import_module(f"libbench.{vendor}")
    return getattr(vendor_module, "Link" if not simulate else "SimulatorLink")


if __name__ == "__main__":
    print_hl("Quantum Benchmarking Suite", color="cyan")

    # arguments
    parser = argparse.ArgumentParser(description="Quantum Benchmark")
    parser.add_argument("vendor", metavar="VENDOR", type=str, help=f"backend to use; one of {', '.join(VENDORS)}")
    parser.add_argument("-i", action="store_true", help="show vendor info")
    parser.add_argument("-s", action="store_true", help="simulate")
    parser.add_argument("--benchmark", metavar="BENCHMARK", type=str, help=f"benchmark to run; one of {', '.join(BENCHMARKS)}")

    args = parser.parse_args()
    print(args)

    VENDOR = args.vendor.lower()
    INFO = args.i
    SIMULATE = args.s
    BENCHMARK = args.benchmark

    assert VENDOR in VENDORS, "vendor does not exist"
    assert BENCHMARK is None or BENCHMARK in BENCHMARKS, "benchmark does not exist"

    # pick backend
    Link = import_link(VENDOR, SIMULATE)

    # pick command
    if INFO:
        info(Link())

    if BENCHMARK:
        Benchmark = import_benchmark(BENCHMARK, VENDOR)
        run(Benchmark(), Link())

    if not INFO and not BENCHMARK:
        parser.print_help()
