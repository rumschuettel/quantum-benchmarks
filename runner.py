#!/usr/bin/env python

import argparse
import glob
import importlib
import os

from libbench import VendorBenchmark, VendorLink, VendorJobManager, print_hl

"""
    Import Functionality for benchmarks, links and jobmanagers
"""
def import_benchmark(name, vendor, simulate, device):
    # handle benchmark selection edge cases:
    if vendor == "ibm" and simulate and device == "qasm_simulator":
        simulate = False

    benchmark_module = importlib.import_module(f"benchmarks.{name}.{vendor}")
    return getattr(
        benchmark_module, "Benchmark" if not simulate else "SimulatedBenchmark"
    )


def import_link(vendor, simulate):
    vendor_module = importlib.import_module(f"libbench.{vendor}")
    return getattr(vendor_module, "Link" if not simulate else "SimulatorLink")


def import_jobmanager(vendor):
    vendor_module = importlib.import_module(f"libbench.{vendor}")
    return getattr(vendor_module, "JobManager")

"""
    Benchmark step
"""
def _run_update(
    jobmanager: VendorJobManager, device: object, additional_stored_info: dict
):
    result = jobmanager.update(device, additional_stored_info=additional_stored_info)

    if result is not None:
        print(result)

    else:
        print(
            f"benchmark not done. Resume by calling ./runner.py --resume {jobmanager.ID}"
        )

"""
    Run mode of ./runner.py
"""

def resume_benchmark(args):
    JOBMANAGER_ID = args.jobmanager_id
    slug = VendorJobManager.load(JOBMANAGER_ID)
    jobmanager = slug.jobmanager

    # restore stuff saved along job manager to recreate device where we run the benchmark on
    VENDOR, DEVICE, SIMULATE = (
        slug.additional_stored_info["vendor"],
        slug.additional_stored_info["device"],
        slug.additional_stored_info["simulate"],
    )
    link = import_link(VENDOR, SIMULATE)()
    device = link.get_device(DEVICE)

    # run update
    _run_update(
        jobmanager, device, {"vendor": VENDOR, "simulate": SIMULATE, "device": DEVICE}
    )


def info(args):
    VENDOR = args.vendor.lower()
    SIMULATE = args.s

    # pick vendor
    link = import_link(VENDOR, SIMULATE)()

    print("available devices:")
    for name in link.get_devices():
        print(name)


def new_benchmark(args):
    VENDOR = args.vendor.lower()
    DEVICE = args.device.lower()
    BENCHMARK = args.benchmark
    SIMULATE = args.s

    assert VENDOR in VENDORS, "vendor does not exist"
    assert BENCHMARK is None or BENCHMARK in BENCHMARKS, "benchmark does not exist"

    # pick vendor
    Link = import_link(VENDOR, SIMULATE)
    link = Link()

    # check device exists
    assert DEVICE in link.get_devices(), "device does not exist"

    device = link.get_device(DEVICE)
    Benchmark = import_benchmark(BENCHMARK, VENDOR, SIMULATE, DEVICE)
    JobManager = import_jobmanager(VENDOR)
    jobmanager = JobManager(Benchmark())

    # run update
    _run_update(
        jobmanager, device, {"vendor": VENDOR, "simulate": SIMULATE, "device": DEVICE}
    )




# find runnable test modules and vendors
BENCHMARKS = [
    os.path.basename(folder)
    for folder in glob.glob("./benchmarks/*")
    if os.path.isdir(folder) and not os.path.basename(folder) == "__pycache__"
]
VENDORS = [
    os.path.basename(folder)
    for folder in glob.glob("./libbench/*")
    if os.path.isdir(folder) and not os.path.basename(folder) == "__pycache__"
]


if __name__ == "__main__":
    print_hl("qυanтυм вencнмarĸιng ѕυιтe\n", color="cyan")

    # arguments
    parser = argparse.ArgumentParser(description="Quantum Benchmark")
    subparsers = parser.add_subparsers(help="Show this help")

    # vendor info
    parser_I = subparsers.add_parser("info", help="Device information")
    parser_I.add_argument("-s", action="store_true", help="simulated devices")
    parser_I.add_argument(
        "vendor",
        metavar="VENDOR",
        type=str,
        help=f"vendor to use; one of {', '.join(VENDORS)}",
    )
    parser_I.set_defaults(func=info)

    # new benchmark
    parser_A = subparsers.add_parser("benchmark", help="Run new benchmark")
    parser_A.add_argument("-s", action="store_true", help="simulate")
    parser_A.add_argument(
        "vendor",
        metavar="VENDOR",
        type=str,
        help=f"vendor to use; one of {', '.join(VENDORS)}",
    )
    parser_A.add_argument(
        "device",
        metavar="DEVICE",
        type=str,
        help="device to use with chosen vendor; run ./runner.py info [-s] VENDOR to get a list.",
    )
    parser_A.add_argument(
        "benchmark",
        metavar="BENCHMARK",
        type=str,
        help=f"benchmark to run; one of {', '.join(BENCHMARKS)}",
    )
    parser_A.set_defaults(func=new_benchmark)

    # resume benchmark
    parser_R = subparsers.add_parser("resume", help="Resume old benchmark")
    parser_R.add_argument(
        "jobmanager_id",
        metavar="JOBMANAGER_ID",
        type=str,
        help=f"old jobmanager id; subfolder name in f{VendorJobManager.RUN_FOLDER}",
    )
    parser_R.set_defaults(func=resume_benchmark)

    args = parser.parse_args()
    print(args)

    # correctly parsed? otherwise show help
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

