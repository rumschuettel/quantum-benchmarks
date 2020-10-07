import sys
import pickle
import gc
import datetime
import numpy as np
import os
from qiskit.circuit.parametertable import ParameterTable
from qiskit.circuit.bit import Bit
from qiskit.circuit.register import Register

class ReplaceParameterTable(ParameterTable):
    __slots__ = '__dict__'
old_parametertable = sys.modules['qiskit.circuit.parametertable'].__dict__['ParameterTable']
sys.modules['qiskit.circuit.parametertable'].__dict__['ParameterTable'] = ReplaceParameterTable

old_bit_register = sys.modules['qiskit.circuit.bit'].__dict__['Bit'].register
old_bit_index = sys.modules['qiskit.circuit.bit'].__dict__['Bit'].index
old_bit_hash = sys.modules['qiskit.circuit.bit'].__dict__['Bit'].__hash__
del sys.modules['qiskit.circuit.bit'].__dict__['Bit'].register
del sys.modules['qiskit.circuit.bit'].__dict__['Bit'].index
sys.modules['qiskit.circuit.bit'].__dict__['Bit'].__hash__ = lambda self : hash((self.register, self.index))

old_register_name = sys.modules['qiskit.circuit.register'].__dict__['Register'].name
old_register_size = sys.modules['qiskit.circuit.register'].__dict__['Register'].size
old_register_hash = sys.modules['qiskit.circuit.register'].__dict__['Register'].__hash__
del sys.modules['qiskit.circuit.register'].__dict__['Register'].name
del sys.modules['qiskit.circuit.register'].__dict__['Register'].size
sys.modules['qiskit.circuit.register'].__dict__['Register'].__hash__ = lambda self : hash((type(self), self.name, self.size))

if len(sys.argv) <= 1:
    print("Supply a pickle to resurrect as a command line argument.")
    sys.exit()
filename = sys.argv[1]
print(f"Resurrecting {filename}...")
with open(filename, 'rb') as f:
    obj = pickle.load(f)
print("Loaded the pickle succesfully.")

sys.modules['qiskit.circuit.parametertable'].__dict__['ParameterTable'] = old_parametertable
sys.modules['qiskit.circuit.bit'].__dict__['Bit'].register = old_bit_register
sys.modules['qiskit.circuit.bit'].__dict__['Bit'].index = old_bit_index
sys.modules['qiskit.circuit.bit'].__dict__['Bit'].__hash__ = old_bit_hash
sys.modules['qiskit.circuit.register'].__dict__['Register'].name = old_register_name
sys.modules['qiskit.circuit.register'].__dict__['Register'].size = old_register_size
sys.modules['qiskit.circuit.register'].__dict__['Register'].__hash__ = old_register_hash

TYPES_TO_SKIP = (str,int,float,bool,datetime.timedelta,np.complex128)
def iterate_obj(o):
    if isinstance(o, dict):
        for k,v in o.items(): o[iterate_obj(k)] = iterate_obj(v)
        return o
    elif isinstance(o, list):
        for i,e in enumerate(o): o[i] = iterate_obj(e)
        return o
    elif isinstance(o, set): return set(iterate_obj(e) for e in o)
    elif isinstance(o, TYPES_TO_SKIP): return o
    elif o is None: return o
    elif type(o).__name__ == "QuantumCircuit": return "Was saved in an obsolete format, so it is deleted."

    # Iterate over the children
    for x in dir(o):
        if x.startswith('__'): continue
        if isinstance(getattr(o,x),TYPES_TO_SKIP): continue
        if type(getattr(o,x)).__name__ in ['method','builtin_function_or_method','function','_abc_data']: continue
        if x == '_MutableMapping__marker': continue
        setattr(o,x,iterate_obj(getattr(o,x)))
    return o
obj = iterate_obj(obj)

os.rename(filename, filename + '_old')
with open(filename, 'wb') as f:
    pickle.dump(obj, f)
