#!/usr/bin/env python

import argparse



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Quantum Benchmark')
    parser.add_argument('vendor', metavar='VENDOR', type=str, help='rigetti or ibm')
    parser.add_argument('--test', metavar="TEST", type=str, default="*", help="test to run")

    args = parser.parse_args()

    print(args)
    
    assert args.vendor in ["rigetti", "ibm"], "invalid vendor. Set to rigetti or ibm"

    if args.vendor == "rigetti":
        from bench import RigettiJobManager as JobManager
    # TODO add IBM
    
    JobManager.test()

