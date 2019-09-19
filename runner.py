#!/usr/bin/env python

import libbench
from libbench import VendorLink, VendorBenchmark, print_hl

import argparse


def test(link: VendorLink):
    print("available backends:")
    for device in link.list_devices():
        print(device)


if __name__ == "__main__":
    print_hl("Quantum Benchmarking Suite", color="cyan")

    # arguments
    parser = argparse.ArgumentParser(description="Quantum Benchmark")
    parser.add_argument("vendor", metavar="VENDOR", type=str, help="ibm, ibm-sim, rigetti or google")
    parser.add_argument("-t", action="store_true")

    args = parser.parse_args()
    print(args)

    VENDOR = args.vendor.lower()
    TEST = args.t

    # pick backend
    if VENDOR == "rigetti":
        from libbench.rigetti import RigettiLink as Link
    elif VENDOR == "ibm":
        from libbench.ibm import IBMLink as Link
    elif VENDOR == "ibm-sim":
        from libbench.ibm import IBMSimulatorLink as Link
    elif VENDOR == "google":
        from libbench.google import GoogleLink as Link
    else:
        raise "Invalid vendor. Valid options are ibm, rigetti or google."

    # pick command
    if TEST:
        test(Link())

    else:
        parser.print_help()
