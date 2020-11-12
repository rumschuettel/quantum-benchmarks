from termcolor import colored
import os, binascii, time, sys


def benchmark_id(rnd_len=2):
    datepart = time.strftime("%Y-%m-%d--%H-%M")
    rndpart = binascii.b2a_hex(os.urandom(rnd_len)).decode("ascii")
    return f"{datepart}--{rndpart}"


def print_hl(*args, color="yellow", bold=False, **kwargs):
    print(
        *[colored(arg, color, attrs=[] if not bold else ["bold"]) for arg in args],
        **kwargs,
    )


def print_stderr(*args):
    print(*args, file=sys.stderr)


def is_power_of_2(num):
    return num != 0 and ((num & (num - 1)) == 0)
