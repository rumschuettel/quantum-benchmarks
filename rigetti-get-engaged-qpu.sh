#!/usr/bin/env python3

from typing import Optional
import sys

from rpcq import Client
from pyquil.api._config import PyquilConfig

def get_engaged_qpu() -> Optional[str]:
    """
        get engaged QPU or None
    """
    try:
        rq = Client(endpoint=PyquilConfig().qpu_compiler_url, timeout=1)
        return rq.call("get_config_info")["lattice_name"]
    except:
        return None


qpu = get_engaged_qpu()
if qpu is not None:
    print(qpu)
    sys.exit(0)
else:
    sys.exit(1)

