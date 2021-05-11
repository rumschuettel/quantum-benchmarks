import itertools as it
from functools import reduce

import numpy as np
from math import pi
from numpy import arccos, sqrt
import random as random
import pyquil as pq
from pyquil.quil import Pragma


from libbench.rigetti import Job as RigettiJob

from .. import PlatonicFractalsBenchmarkMixin


class RigettiPlatonicFractalsJob(RigettiJob):
    @staticmethod
    def job_factory(body, strength, num_steps, num_shots, shots_multiplier, add_measurements):
        for m_idx in range(shots_multiplier):
            for dirs in it.product(*[range(1, 4)] * num_steps):
                yield RigettiPlatonicFractalsJob(
                    body, strength, dirs, 2, num_shots, m_idx, add_measurements
                )
                yield RigettiPlatonicFractalsJob(
                    body, strength, dirs, 3, num_shots, m_idx, add_measurements
                )

    def __init__(self, body, strength, meas_dirs, final_meas_dir, shots, m_idx, add_measurements):
        super().__init__()

        self.body = body
        self.strength = strength
        self.meas_dirs = meas_dirs
        self.final_meas_dir = final_meas_dir
        self.shots = shots
        self.m_idx = m_idx
        self.add_measurements = add_measurements

        if not body == 0:  # PlatonicFractalsBenchmarkMixin.BODY_OCTA
            raise NotImplementedError("This fractal is not yet implemented!")

        # Calculate some parameters
        angle1 = arccos(sqrt((1 + strength) / 2))

        # Build the circuit
        program = pq.Program()

        program += pq.gates.H(0)
        for i in range(len(meas_dirs)):
            if meas_dirs[i] == 2:
                program += pq.gates.S(0).dagger()
            if meas_dirs[i] == 1 or meas_dirs[i] == 2:
                program += pq.gates.H(0)

            program += pq.gates.H(i + 1)
            program += pq.gates.RZ(2 * angle1, i + 1)

            program += pq.gates.RZ(2 * (pi / 2 - 2 * angle1), i + 1).controlled(0)
            program += pq.gates.H(i + 1)

            if meas_dirs[i] == 1 or meas_dirs[i] == 2:
                program += pq.gates.H(0)
            if meas_dirs[i] == 2:
                program += pq.gates.S(0)
        if final_meas_dir == 2:
            program += pq.gates.S(0).dagger()
        if final_meas_dir == 1 or final_meas_dir == 2:
            program += pq.gates.H(0)

        # store the resulting circuit
        self.program = program

    def run(self, device):
        super().run(device)
        return device.execute(self.program, num_shots=self.shots)

    def __str__(self):
        return f"ForestPlatonicFractalsJob--{self.strength}-{self.meas_dirs}-{self.final_meas_dir}-{self.m_idx}"
