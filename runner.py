#!/usr/bin/env python

import libbench

import argparse


def test(link):
    link.test()


if __name__ == "__main__":
    # arguments
    parser = argparse.ArgumentParser(description="Quantum Benchmark")
    parser.add_argument("vendor", metavar="VENDOR", type=str, help="rigetti or ibm")
    parser.add_argument("-t", action="store-true")

    args = parser.parse_args()
    print(args)

    VENDOR = args.vendor.lower()
    TEST = args.test

    # pick backend
    if VENDOR == "rigetti":
        from libbench.rigetti import RigettiLink as Link
    elif VENDOR == "ibm":
        from libbench.ibm import IBMLink as Link
    elif VENDOR == "google":
        from libbench.google import GoogleLink as Link
    else:
        raise "Invalid vendor. Valid options are ibm, google, rigetti."

    # pick command
    if TEST:
        test(Link())

    else:
        parser.print_help()
