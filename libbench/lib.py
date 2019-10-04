from termcolor import colored
import os, binascii, time


def benchmark_id(rnd_len=5):
    datepart = time.strftime("%Y-%m-%d--%H-%M")
    rndpart = binascii.b2a_hex(os.urandom(rnd_len)).decode("ascii")
    return f"bench-{datepart}--{rndpart}"


def print_hl(*args, color="yellow", **kwargs):
    print(*[colored(arg, color) for arg in args], **kwargs)
