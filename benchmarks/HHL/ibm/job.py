import itertools as it
from functools import reduce

import numpy as np
from math import pi
from numpy import arccos, sqrt
import random as random
from qiskit import QuantumCircuit

from qiskit import *
from qiskit.circuit.library.standard_gates import *

from libbench.ibm import Job as IBMJob

from .. import HHLBenchmarkMixin


class HHLJob(IBMJob):
    @staticmethod
    def create_qsvt_circuit(num_qubits, num_ancillas, add_measurements, block_encoding, angles):
        qsvt_circuit = (
            QuantumCircuit(num_qubits+num_ancillas+1, num_qubits+num_ancillas+1)
            if add_measurements
            else QuantumCircuit(num_qubits+num_ancillas+1)           
        )       
        if num_ancillas != 1:      
            raise NotImplementedError("The general QSVT circuit generation is not yet implemented!")
        else:
            block_encoding_inv=block_encoding.inverse()             
            qubits=list(range(1,num_qubits + num_ancillas + 1))

            # Quanutm Singular Value Transformation
            qsvt_circuit.h(0)
            for i in range(0,len(angles)):
                if i % 2 == 0:
                    qsvt_circuit.compose(block_encoding,qubits=qubits,inplace=True)
                else:
                    qsvt_circuit.compose(block_encoding_inv,qubits=qubits,inplace=True)                 
                qsvt_circuit.x(1)
                qsvt_circuit.cx(1,0) 
                qsvt_circuit.rz(-2*angles[i],0)         
                # For debugging purposes to get the global phase right replace the above line with the following:
                # qsvt_circuit.u1(-angles[i],0)     
                # qsvt_circuit.x(0)           
                # qsvt_circuit.u1(angles[i],0)  
                # qsvt_circuit.x(0)                                   
                qsvt_circuit.cx(1,0)                
                qsvt_circuit.x(1)                       
            qsvt_circuit.h(0)

            return qsvt_circuit


    @staticmethod
    def job_factory(block_encoding, num_qubits, num_ancillas, qsvt_poly, num_shots, shots_multiplier, add_measurements):          
        if num_ancillas != 1 or not (qsvt_poly is None):           
            raise NotImplementedError("The general HHL circuit generations is not yet implemented!")
        elif (qsvt_poly is None):
            # Build block-encoding of A  
            block_encoding = QuantumCircuit(num_qubits+num_ancillas)
            if num_qubits==1:  
                block_encoding.append(SwapGate().power(0.5),[0,1])
                block_encoding.ry(-pi/4,0)
                block_encoding.rx(-pi/3,1)

                # Angles describing the polynomial inverting A
                angles= (-2.279330633470087101821688078684, -2.27933063347008710182168807868, -7.05851428429600138350129876836)

                qsvt_circuit = HHLJob.create_qsvt_circuit(num_qubits, num_ancillas, add_measurements, block_encoding.inverse(), angles)

                # For debug purposes
                # reorder = QuantumCircuit(num_qubits+num_ancillas+1)   
                # reorder.swap(0,2)
       
            elif num_qubits==2:
                block_encoding.ry(-pi/8,0)
                block_encoding.rx(-pi/4,1)
                block_encoding.rz(-pi/2,2) 
                block_encoding.cx(1, 0)
                block_encoding.z(2)
                block_encoding.x(0)             
                block_encoding.cx(2, 1)
                block_encoding.rx(-pi/2,0)
                block_encoding.ry(-pi/4,1)
                block_encoding.rz(-pi/8,2)
                block_encoding.cx(1, 0)
                block_encoding.z(2)  
                block_encoding.ry(-pi/8,0)
                block_encoding.rx(-pi/4,1)
                block_encoding.ry(-pi/2,2)   
                block_encoding.z(0)             
                block_encoding.cx(2, 1)
                block_encoding.ry(-pi/2,0)
                block_encoding.rz(-pi/4,1)
                block_encoding.rx(-pi/8,2)                                               
                block_encoding.cx(1, 0)
                block_encoding.x(2)
                # Just global phase for debugging
                # block_encoding.u1(7* pi /16, 0)
                # block_encoding.x(0)
                # block_encoding.u1(7* pi /16, 0)
                # block_encoding.x(0) 

                # Angles describing the polynomial inverting A
                angles=(-1.2329906360794255512184231493, -1.45745010323350887868278909, -1.5025688694325865597661246, -1.78673547240229808944153, \
                        -1.7867354724022980894415, -1.502568869432586559766, -1.45745010323350887868, -1.2329906360794255512, 0.8088518475393644255)         

                # Quanutm Singular Value Transformation
                qsvt_circuit = HHLJob.create_qsvt_circuit(num_qubits, num_ancillas, add_measurements, block_encoding.inverse(), angles)

                # For debug purposes
                # reorder = QuantumCircuit(num_qubits+num_ancillas+1)   
                # reorder.swap(0,3)        
                # reorder.swap(1,2)                

            else:
                raise NotImplementedError("The general HHL circuit generations is not yet implemented!")
            
            # Debugging the circuit      
            # print(block_encoding)
            # print_unitary=reorder.compose(block_encoding,qubits=list(range(1,num_qubits + num_ancillas + 1))).extend(reorder)
            # #job execution and getting the unitary matrix of the circuit
            # job = execute(print_unitary, qiskit.Aer.get_backend('unitary_simulator'))
            # print(job.result().get_unitary(print_unitary, decimals=2))     

            # Debugging the circuit
            # print(qsvt_circuit)
            # print_unitary=reorder.combine(qsvt_circuit).extend(reorder)
            # # job execution and getting the unitary matrix of the circuit
            # job = execute(print_unitary, qiskit.Aer.get_backend('unitary_simulator'))
            # print(job.result().get_unitary(print_unitary, decimals=2))   

       

        for m_idx in range(shots_multiplier):
            for basis_vec in range(0, 2**num_qubits):
                instance_circuit = (
                    QuantumCircuit(num_qubits+num_ancillas+1, num_qubits+num_ancillas+1)
                    if add_measurements
                    else QuantumCircuit(num_qubits+num_ancillas+1)
                )
                if basis_vec % 2 == 1:
                    instance_circuit.x(num_qubits+num_ancillas) 
                if basis_vec % 4 >= 2 and num_qubits > 1:       
                    instance_circuit.x(num_qubits+num_ancillas-1)    
                instance_circuit.extend(qsvt_circuit)                                                                           
                yield HHLJob(
                    instance_circuit, num_qubits, num_ancillas, basis_vec, num_shots, m_idx, add_measurements
                )

    def __init__(self, circuit, num_qubits, num_ancillas, basis_vec, shots, m_idx, add_measurements):
        super().__init__()

        self.circuit = circuit
        self.num_qubits = num_qubits      
        self.num_ancillas = num_ancillas            
        self.basis_vec = basis_vec
        self.shots = shots
        self.m_idx = m_idx
        self.add_measurements = add_measurements

        if add_measurements:
            circuit.measure(
                # list(range(num_qubits+num_ancillas+1)), list(range(num_qubits+num_ancillas+1))                
                list(range(num_qubits+num_ancillas+1)), list(reversed(range(num_qubits+num_ancillas+1)))
            )        

    def run(self, device):
        super().run(device)
        return device.execute(self.circuit, num_shots=self.shots)

    def __str__(self):
        return f"IBMHHLJob--{self.num_qubits}-{self.basis_vec}-{self.shots}-{self.m_idx}"
