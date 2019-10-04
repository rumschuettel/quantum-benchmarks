#!/usr/bin/env python

import argparse
import glob
import importlib
import os
import pickle
import matplotlib.pyplot as plt

from libbench import VendorBenchmark, VendorLink, VendorJobManager, print_hl


"""
    Definitions of constants
"""


MODE_CLASS_NAMES = {
    'cloud' : 'Cloud',
    'measure_local' : 'MeasureLocal',
    'statevector' : 'Statevector'
}

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
MODES = list(MODE_CLASS_NAMES.keys())

VISUALIZATION_FILENAME = "visualization.eps"


"""
    Import Functionality for benchmarks, links and jobmanagers
"""


def import_benchmark(name, vendor, mode, device):
    benchmark_module = importlib.import_module(f"benchmarks.{name}.{vendor}")
    return getattr(benchmark_module, "Benchmark" if mode != "Statevector" else "SimulatedBenchmark")


def import_link(vendor, mode):
    vendor_module = importlib.import_module(f"libbench.{vendor}")
    return getattr(vendor_module, mode + "Link")


def import_jobmanager(vendor):
    vendor_module = importlib.import_module(f"libbench.{vendor}")
    return getattr(vendor_module, "JobManager")


def import_argparser(name, toadd):
    benchmark_module = importlib.import_module(f"benchmarks.{name}")
    argparser = getattr(benchmark_module, "argparser")
    return argparser(toadd)


def import_paramparser(name):
    benchmark_module = importlib.import_module(f"benchmarks.{name}")
    return getattr(benchmark_module, "paramparser")


def import_visualize_function(name):
    benchmark_module = importlib.import_module(f"benchmarks.{name}")
    return getattr(benchmark_module, "default_visualization")


"""
    Benchmark step
"""


def _run_update(jobmanager: VendorJobManager, device: object, additional_stored_info: dict, visualize: bool = False):
    result = jobmanager.update(device, additional_stored_info=additional_stored_info)

    if result is not None:
        print()
        print("Collated result:")
        print(result)
        if visualize:
            fig = handle_visualization(jobmanager.ID)
            if isinstance(fig, plt.Figure):
                plt.show()
            else:
                print("Could not display the visualization as the result was not a figure.")

    else:
        print(f"benchmark not done. Resume by calling ./runner.py resume {jobmanager.ID}")


"""
    Run mode of ./runner.py
"""


def obtain_jobmanager(args):
    JOBMANAGER_ID = args.jobmanager_id
    slug = VendorJobManager.load(JOBMANAGER_ID)
    jobmanager = slug["jobmanager"]

    # restore stuff saved along job manager to recreate device where we run the benchmark on
    VENDOR, DEVICE, MODE = (
        slug["additional_stored_info"]["vendor"],
        slug["additional_stored_info"]["device"],
        slug["additional_stored_info"]["mode"],
    )
    link = import_link(VENDOR, MODE)()
    device = link.get_device(DEVICE)

    jobmanager.thaw(device)

    return jobmanager, device, slug

def resume_benchmark(args):
    jobmanager, device, slug = obtain_jobmanager(args)

    # run update
    _run_update(jobmanager, device, slug['additional_stored_info'])


def print_status(args):
    jobmanager, *_ = obtain_jobmanager(args)

    # print the status message
    jobmanager.print_status()


"""
    Vendor information helper function
"""


def info_vendor(args):
    VENDOR = args.vendor.lower()

    for mode, MODE in MODE_CLASS_NAMES.items():
        link = import_link(VENDOR, MODE)()
        devices = link.get_devices()
        print(f"Available {mode} devices:")
        if len(devices) == 0:
            print_hl("No devices available.", color='red')
        else:
            for name in devices:
                print(name)
        print()


"""
    Benchmark information helper function
"""


def info_benchmark(parser_benchmarks, args):
    BENCHMARK = args.benchmark
    assert BENCHMARK in BENCHMARKS

    argparser = parser_benchmarks[BENCHMARK]
    argparser.print_help()


"""
    New benchmark starter function
"""


def new_benchmark(args):
    VENDOR = args.vendor.lower()
    DEVICE = args.device.lower()
    BENCHMARK = args.benchmark
    VISUALIZE = args.visualize
    MODE = MODE_CLASS_NAMES[args.mode]

    assert VENDOR in VENDORS, "vendor does not exist"
    assert BENCHMARK is None or BENCHMARK in BENCHMARKS, "benchmark does not exist"

    # pick vendor
    Link = import_link(VENDOR, MODE)
    link = Link()

    # check device exists
    assert DEVICE in link.get_devices(), "device does not exist"

    paramparser = import_paramparser(BENCHMARK)
    params = paramparser(args)

    device = link.get_device(DEVICE)
    Benchmark = import_benchmark(BENCHMARK, VENDOR, MODE, DEVICE)
    JobManager = import_jobmanager(VENDOR)
    jobmanager = JobManager(Benchmark(**params))

    # run update
    _run_update(jobmanager, device, {
        "vendor": VENDOR,
        "mode": MODE,
        "device": DEVICE,
        "benchmark": BENCHMARK,
        **params
    }, visualize = VISUALIZE)


"""
    Visualization functions
"""


def handle_visualization(JOB_ID):
    folder = f"{VendorJobManager.RUN_FOLDER}/{JOB_ID}"
    collated_file = pickle.load(open(f"{folder}/{VendorJobManager.COLLATED_FILENAME}", 'rb'))
    collated_result, additional_stored_info = (
        collated_file['collated_result'],
        collated_file['additional_stored_info']
    )
    BENCHMARK = additional_stored_info['benchmark']
    visualize_function = import_visualize_function(BENCHMARK)
    fig = visualize_function(collated_result, additional_stored_info)
    visualization_file = f"{folder}/{VISUALIZATION_FILENAME}"
    fig.savefig(visualization_file)
    print(f"Wrote the visualization of {JOB_ID} to {visualization_file}.")
    return fig


def visualize(args):
    JOB_IDS = args.job_ids
    if len(JOB_IDS) == 0:
        print("No job ids supplied, so displaying a list of available job ids.")
        print("Color coding: ", end = '')
        print_hl('running', color = 'red', end = '')
        print(', ', end = '')
        print_hl('done, no visualzation available', color = 'yellow', end = '')
        print(', ', end = '')
        print_hl('done, visualization available', color = 'green', end = '')
        print('.')
        for folder in glob.glob("./runs/*"):
            if os.path.isdir(folder) and not os.path.basename(folder) == "__pycache__":
                collated_filepath = f"{folder}/{VendorJobManager.COLLATED_FILENAME}"
                JOB_ID = os.path.basename(folder)
                if os.path.isfile(collated_filepath):
                    collated_file = pickle.load(open(f"{folder}/{VendorJobManager.COLLATED_FILENAME}", 'rb'))
                    additional_stored_info = collated_file['additional_stored_info']
                    color = 'green' if os.path.isfile(f"{folder}/{VISUALIZATION_FILENAME}") else "yellow"
                    print_hl(JOB_ID, additional_stored_info, color = color)
                else:
                    print_hl(JOB_ID, color = 'red')
    else:
        for JOB_ID in JOB_IDS:
            handle_visualization(JOB_ID)


if __name__ == "__main__":
    print_hl("qυanтυм вencнмarĸιng ѕυιтe\n", color="cyan")

    # arguments
    parser = argparse.ArgumentParser(description="Quantum Benchmark")
    subparsers = parser.add_subparsers(metavar="ACTION", help="Action you want to take")

    # new benchmark
    parser_A = subparsers.add_parser("benchmark", help="Run new benchmark")
    parser_A.set_defaults(func=new_benchmark)
    parser_A.add_argument(
        "vendor",
        metavar="VENDOR",
        type=str,
        help=f"vendor to use; one of {', '.join(VENDORS)}"
    )
    parser_A.add_argument(
        "mode",
        metavar="MODE",
        type=str,
        help=f"mode to run; one of {', '.join(MODES)}"
    )
    parser_A.add_argument(
        "device",
        metavar="DEVICE",
        type=str,
        help="device to use with chosen vendor; run ./runner.py info vendor VENDOR to get a list.",
    )
    parser_A.add_argument(
        "--visualize",
        action="store_true",
        help="show the visualization if the benchmark completes directly."
    )
    subparsers_A = parser_A.add_subparsers(metavar="BENCHMARK", help="benchmark to run")

    parser_benchmarks = {}
    for benchmark in BENCHMARKS:
        parser_benchmark = import_argparser(benchmark, subparsers_A)
        parser_benchmark.set_defaults(benchmark=benchmark)
        parser_benchmarks[benchmark] = parser_benchmark

    # info
    parser_I = subparsers.add_parser("info", help="Request information")
    parser_I.set_defaults(func=lambda args : parser_I.print_help())
    subparsers_I = parser_I.add_subparsers(metavar="TYPE", help="Type of information requested")

    # vendor info
    parser_IV = subparsers_I.add_parser("vendor", help="Information about devices")
    parser_IV.set_defaults(func=info_vendor)
    parser_IV.add_argument(
        "vendor",
        metavar="VENDOR",
        type=str,
        default=False,
        help=f"vendor to use; one of {', '.join(VENDORS)}"
    )

    # benchmark info
    parser_IB = subparsers_I.add_parser("benchmark", help="Information about benchmarks")
    parser_IB.set_defaults(func=lambda args: info_benchmark(parser_benchmarks,args))
    parser_IB.add_argument(
        "benchmark",
        metavar="BENCHMARK",
        type=str,
        help=f"benchmark to use; one of {', '.join(BENCHMARKS)}"
    )

    # resume benchmark
    parser_R = subparsers.add_parser("resume", help="Resume old benchmark")
    parser_R.set_defaults(func=resume_benchmark)
    parser_R.add_argument(
        "jobmanager_id",
        metavar="JOBMANAGER_ID",
        type=str,
        help=f"old jobmanager id; subfolder name in f{VendorJobManager.RUN_FOLDER}",
    )

    parser_V = subparsers.add_parser("visualize", help="Visualize completed benchmarks")
    parser_V.set_defaults(func=visualize)
    parser_V.add_argument("job_ids", nargs='*')

    parser_S = subparsers.add_parser("status", help="Display the status of a benchmark.")
    parser_S.add_argument(
        "jobmanager_id",
        metavar="JOBMANAGER_ID",
        type=str,
        help=f"old jobmanager id; subfolder name in f{VendorJobManager.RUN_FOLDER}"
    )
    parser_S.set_defaults(func=print_status)

    args = parser.parse_args()

    # correctly parsed? otherwise show help
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
