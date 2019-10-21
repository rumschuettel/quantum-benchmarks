#!/usr/bin/env python3

import argparse
import glob
import importlib
import os
import pickle
import matplotlib

DEFAULT_MPL_BACKEND = matplotlib.get_backend()
matplotlib.use("Cairo")  # backend without X server requirements
import matplotlib.pyplot as plt

from libbench import VendorBenchmark, VendorLink, VendorJobManager, print_hl


"""
    Definitions of constants
"""

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

MODE_CLASS_NAMES = {
    "cloud": "Cloud",
    "measure_local": "MeasureLocal",
    "statevector": "Statevector",
}
MODES = list(MODE_CLASS_NAMES.keys())


"""
    Import Functionality for benchmarks, links and jobmanagers
"""


def import_benchmark(name, vendor, mode, device):
    benchmark_module = importlib.import_module(f"benchmarks.{name}.{vendor}")
    return getattr(
        benchmark_module, "SimulatedBenchmark" if mode == "Statevector" else "Benchmark"
    )


def import_link(vendor, mode):
    vendor_module = importlib.import_module(f"libbench.{vendor}")
    return getattr(vendor_module, mode + "Link")


def import_jobmanager(vendor):
    vendor_module = importlib.import_module(f"libbench.{vendor}")
    return getattr(vendor_module, "JobManager")


def import_argparser(name, toadd, **argparse_options):
    benchmark_module = importlib.import_module(f"benchmarks.{name}")
    argparser = getattr(benchmark_module, "argparser")
    return argparser(toadd, **argparse_options)


def obtain_jobmanager(job_id, run_folder, recreate_device):
    VendorJobManager.RUN_FOLDER = run_folder
    slug = VendorJobManager.load(job_id)
    jobmanager = slug["jobmanager"]

    # restore stuff saved along job manager to recreate device where we run the benchmark on
    VENDOR, DEVICE, MODE = (
        slug["additional_stored_info"]["vendor"],
        slug["additional_stored_info"]["device"],
        slug["additional_stored_info"]["mode"],
    )

    device = None
    if recreate_device:
        link = import_link(VENDOR, MODE)()
        device = link.get_device(DEVICE)

        jobmanager.thaw(device)

    return jobmanager, device, slug


"""
    INFO
"""


def info_vendor(args):
    VENDOR = args.vendor

    for mode, MODE in MODE_CLASS_NAMES.items():
        link = import_link(VENDOR, MODE)()
        devices = link.get_devices()
        print(f"Available {mode} devices:")
        if len(devices) == 0:
            print_hl("No devices available.", color="red")
        else:
            for name in devices:
                print(name)
        print()


def info_benchmark(parser_benchmarks, args):
    BENCHMARK = args.benchmark
    assert BENCHMARK in BENCHMARKS

    argparser = parser_benchmarks[BENCHMARK]
    argparser.print_help()


"""
    BENCHMARK and RESUME
"""


def _show_figure(figpath):
    import webbrowser

    webbrowser.open_new(str(figpath))


def _run_update(
    jobmanager: VendorJobManager,
    device: object,
    additional_stored_info: dict,
    show_directly: bool = False,
):
    if not jobmanager.update(
        device,
        additional_stored_info=additional_stored_info,
        figure_callback=_show_figure if show_directly else lambda *x: None,
    ):
        print(
            f"benchmark not done. Resume by calling ./runner.py resume {jobmanager.ID}"
        )


def resume_benchmark(args):
    RUN_FOLDER = args.run_folder
    JOB_ID = args.job_id
    jobmanager, device, slug = obtain_jobmanager(
        JOB_ID, RUN_FOLDER, recreate_device=True
    )

    # run update
    _run_update(jobmanager, device, slug["additional_stored_info"])


def new_benchmark(args):
    VENDOR = args.vendor
    DEVICE = args.device
    BENCHMARK = args.benchmark
    MODE = MODE_CLASS_NAMES[args.mode]
    RUN_FOLDER = (
        args.run_folder
    )  # we do not validate this since the folder is created on-the-fly

    assert VENDOR in VENDORS, "vendor does not exist"
    assert BENCHMARK is None or BENCHMARK in BENCHMARKS, "benchmark does not exist"

    # pick vendor
    Link = import_link(VENDOR, MODE)
    link = Link()

    # check device exists
    assert DEVICE in link.get_devices(), "device does not exist"

    device = link.get_device(DEVICE)
    Benchmark = import_benchmark(BENCHMARK, VENDOR, MODE, DEVICE)
    JobManager = import_jobmanager(VENDOR)
    JobManager.RUN_FOLDER = RUN_FOLDER
    jobmanager = JobManager(Benchmark(**vars(args)))

    # run update
    _run_update(
        jobmanager,
        device,
        additional_stored_info={
            "vendor": VENDOR,
            "mode": MODE,
            "device": DEVICE,
            "benchmark": BENCHMARK,
        },
        show_directly=args.show_directly,
    )


"""
    REFRESH
"""


def _get_job_ids(run_folder):
    return [
        os.path.basename(folder)
        for folder in glob.glob(f"{run_folder}/*")
        if os.path.isdir(folder) and not os.path.basename(folder) == "__pycache__"
    ]


def refresh(args):
    RUN_FOLDER = args.run_folder
    ALL = args.all
    job_ids = args.job_ids if not ALL else _get_job_ids(RUN_FOLDER)

    for JOB_ID in job_ids:
        print(f"refreshing {JOB_ID}...", end=" ")
        jobmanager, *_ = obtain_jobmanager(JOB_ID, RUN_FOLDER, recreate_device=False)

        if jobmanager.done:
            jobmanager.finalize()
            print("done.")
        else:
            print("not done yet.")


"""
    STATUS
"""


def status(args):
    RUN_FOLDER = args.run_folder
    VendorJobManager.print_legend()

    for job_id in _get_job_ids(RUN_FOLDER):
        jobmanager, _, slug = obtain_jobmanager(
            job_id, RUN_FOLDER, recreate_device=False
        )
        jobmanager.print_status(tail=slug["additional_stored_info"])


if __name__ == "__main__":
    print_hl("qυanтυм вencнмarĸιng ѕυιтe\n", color="cyan")

    # arguments
    argparse_options = {"formatter_class": argparse.ArgumentDefaultsHelpFormatter}
    parser = argparse.ArgumentParser(
        description="Quantum Benchmark", **argparse_options
    )
    subparsers = parser.add_subparsers(metavar="ACTION", help="Action you want to take")

    # new benchmark
    parser_A = subparsers.add_parser(
        "benchmark", help="Run new benchmark", **argparse_options
    )
    parser_A.set_defaults(func=new_benchmark)
    parser_A.add_argument(
        "vendor",
        metavar="VENDOR",
        type=str,
        help=f"vendor to use; one of {', '.join(VENDORS)}",
    )
    parser_A.add_argument(
        "mode", metavar="MODE", type=str, help=f"mode to run; one of {', '.join(MODES)}"
    )
    parser_A.add_argument(
        "device",
        metavar="DEVICE",
        type=str,
        help="device to use with chosen vendor; run ./runner.py info vendor VENDOR to get a list.",
    )
    parser_A.add_argument(
        "--show_directly",
        action="store_true",
        help="show the visualization if the benchmark completes directly.",
    )
    parser_A.add_argument(
        "--run_folder",
        default=VendorJobManager.RUN_FOLDER,
        help=f"folder to store benchmark jobs in; created if it does not exist",
    )
    subparsers_A = parser_A.add_subparsers(metavar="BENCHMARK", help="benchmark to run")

    parser_benchmarks = {}
    for benchmark in BENCHMARKS:
        parser_benchmark = import_argparser(benchmark, subparsers_A, **argparse_options)
        parser_benchmark.set_defaults(benchmark=benchmark)
        parser_benchmarks[benchmark] = parser_benchmark

    # info
    parser_I = subparsers.add_parser(
        "info", help="Information for vendors or benchmarks", **argparse_options
    )
    parser_I.set_defaults(func=lambda args: parser_I.print_help())
    subparsers_I = parser_I.add_subparsers(
        metavar="TYPE", help="Type of information requested"
    )

    # vendor info
    parser_IV = subparsers_I.add_parser(
        "vendor", help="Information about devices", **argparse_options
    )
    parser_IV.set_defaults(func=info_vendor)
    parser_IV.add_argument(
        "vendor",
        metavar="VENDOR",
        type=str,
        default=False,
        help=f"vendor to use; one of {', '.join(VENDORS)}",
    )

    # benchmark info
    parser_IB = subparsers_I.add_parser(
        "benchmark", help="Information about benchmarks", **argparse_options
    )
    parser_IB.set_defaults(func=lambda args: info_benchmark(parser_benchmarks, args))
    parser_IB.add_argument(
        "benchmark",
        metavar="BENCHMARK",
        type=str,
        help=f"benchmark to use; one of {', '.join(BENCHMARKS)}",
    )

    # resume benchmark
    parser_R = subparsers.add_parser(
        "resume", help="Resume old benchmark", **argparse_options
    )
    parser_R.set_defaults(func=resume_benchmark)
    parser_R.add_argument(
        "job_id",
        metavar="JOB_ID",
        type=str,
        help=f"old job id; subfolder name in f{VendorJobManager.RUN_FOLDER}",
    )
    parser_R.add_argument(
        "--run_folder",
        default=VendorJobManager.RUN_FOLDER,
        help=f"folder to store benchmark jobs in; created if it does not exist",
    )

    # update collation and visualization steps of jobmanager
    parser_V = subparsers.add_parser(
        "refresh",
        help="Update already completed benchmarks from individual job runs.",
        **argparse_options,
    )
    parser_V.set_defaults(func=refresh)
    parser_V.add_argument(
        "--all", action="store_true", help="refresh all completed benchmarks"
    )
    parser_V.add_argument("job_ids", nargs="*")

    # benchmark status
    parser_S = subparsers.add_parser(
        "status", help="Display the status of all benchmarks.", **argparse_options
    )
    parser_S.set_defaults(func=status)
    parser_S.add_argument(
        "--run_folder",
        default=VendorJobManager.RUN_FOLDER,
        help=f"folder to store benchmark jobs in; created if it does not exist",
    )

    args = parser.parse_args()

    # correctly parsed? otherwise show help
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
