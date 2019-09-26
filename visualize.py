#!/usr/bin/env python

import argparse
import glob
import importlib
import os
import pickle
from libbench.lib import print_hl
from libbench.jobmanager import VendorJobManager

def import_visualization_routine(BENCHMARK, func_name = 'default_visualize'):
    benchmark = importlib.import_module(f'benchmarks.{BENCHMARK}')
    return getattr(benchmark, func_name)

def get_job_status_color(JOBMANAGER_ID):
    if os.path.isfile(f'runs/{JOBMANAGER_ID}/collated.pickle'):
        return 'green'
    return 'red'

def get_job_additional_info(JOBMANAGER_ID):
    slug = pickle.load(open(f'runs/{JOBMANAGER_ID}/jobmanager.pickle', 'rb'))
    return slug["additional_info"]

def list_benchmarks(args):
    # Display the runs
    ctr = 0
    if os.path.isdir('runs'):
        for JOBMANAGER_ID in os.listdir('runs'):
            if not os.path.isdir(f'runs/{JOBMANAGER_ID}'): continue
            additional_info = get_job_additional_info(JOBMANAGER_ID)
            VENDOR = additional_info["vendor"]
            SIMULATE = additional_info["simulate"]
            DEVICE = additional_info["device_name"]
            BENCHMARK = additional_info["benchmark"]
            col = get_job_status_color(JOBMANAGER_ID)
            print_hl('\t'.join([JOBMANAGER_ID, VENDOR, DEVICE, BENCHMARK, str(SIMULATE)]), color = col)
            ctr += 1

    # Display that there are no runs, it applicable
    if ctr == 0:
        print_hl("No runs available.", color = 'red')
        return

def visualize(args):
    JOBMANAGER_ID = args.jobmanager_id

    # Check if the file exists
    if not os.path.isfile(f'runs/{JOBMANAGER_ID}/collated.pickle'):
        print_hl("No collated results available for this run.", color = 'red')
        return

    # Get the results
    data = pickle.load(open(f'runs/{JOBMANAGER_ID}/collated.pickle', 'rb'))
    collated_result, additional_info = (
        data["collated_result"],
        data["additional_info"]
    )
    VENDOR, SIMULATE, DEVICE, BENCHMARK = (
        additional_info["vendor"],
        additional_info["simulate"],
        additional_info["device_name"],
        additional_info["benchmark"]
    )

    # Visualize
    visualize_function = import_visualization_routine(BENCHMARK)
    fig = visualize_function(collated_result, additional_info)

    # Save the result
    fig.savefig(f'runs/{JOBMANAGER_ID}/visualization.eps')

if __name__ == "__main__":
    print_hl('𝓺𝓾𝓪𝓷𝓽𝓾𝓶 𝓫𝓮𝓷𝓬𝓱𝓶𝓪𝓻𝓴𝓲𝓷𝓰 𝓿𝓲𝓼𝓾𝓪𝓵𝓲𝔃𝓪𝓽𝓲𝓸𝓷 𝓼𝓾𝓲𝓽𝓮\n', color = 'green')

    parser = argparse.ArgumentParser(description="Quantum Benchmark Visualization")
    subparsers = parser.add_subparsers(help="Show this help")

    parser_V = subparsers.add_parser("visualize", help="Visualization")
    parser_V.add_argument(
        "jobmanager_id",
        metavar="JOBMANAGER_ID",
        type=str,
        help=f"jobmanager id; subfolder name in f{VendorJobManager.RUN_FOLDER}"
    )
    parser_V.set_defaults(func=visualize)

    parser_L = subparsers.add_parser("list", help="List current benchmarks.")
    parser_L.set_defaults(func=list_benchmarks)

    args = parser.parse_args()
    print(args)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
