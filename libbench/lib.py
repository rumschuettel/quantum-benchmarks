from termcolor import colored

def print_hl(*args, color="yellow"):
    print(*[colored(arg, color) for arg in args])