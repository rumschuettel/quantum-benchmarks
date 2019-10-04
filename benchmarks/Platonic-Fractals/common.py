from typing import Dict

import numpy as np
from math import pi
from numpy import arccos,sqrt
import random as random
from pylab import rcParams
from matplotlib import pyplot as plt

from libbench import VendorJob

class PlatonicFractalsBenchmarkMixin:
    BODY_OCTA=0

    def __init__(self, body, strength, num_steps, num_dirs_change, num_shots, random_seed):
        super().__init__()

        self.body = body
        self.strength = strength
        self.num_steps = num_steps
        self.num_dirs_change = num_dirs_change              
        self.num_shots = num_shots  
        self.random_seed = random_seed

        print("Random seed: "+str(random_seed))

    def collate_results(self, results: Dict[VendorJob, object], threshold=300):
        dirStats = {}

        # fill in with values from jobs
        for job in results:
            result = results[job]
            dirs=str(result["dirs"]).strip('[]')
            del result["dirs"]
            if not dirs in dirStats:
                dirStats[dirs] = result
            if "ymeascounts" in result :
                if not "ymeascounts" in dirStats[dirs]:
                    dirStats[dirs].update(result)
                else :
                    for meas in result["ymeascounts"] :
                        if meas not in dirStats[dirs]["ymeascounts"]:
                            dirStats[dirs]["ymeascounts"][meas]=result["ymeascounts"][meas]
                            dirStats[dirs]["ystates"][meas]=result["ystates"][meas]
                        else :
                            total = result["ymeascounts"][meas]+dirStats[dirs]["ymeascounts"][meas]
                            dirStats[dirs]["ystates"][meas]=(result["ymeascounts"][meas]*result["ystates"][meas]+dirStats[dirs]["ymeascounts"][meas]*dirStats[dirs]["ystates"][meas])/total
                            dirStats[dirs]["ymeascounts"][meas]=total
            elif "zmeascounts" in result:
                if not "zmeascounts" in dirStats[dirs]:
                    dirStats[dirs].update(result) 
                else :
                    for meas in result["zmeascounts"] :
                        if meas not in dirStats[dirs]["zmeascounts"]:
                            dirStats[dirs]["zmeascounts"][meas]=result["zmeascounts"][meas]
                            dirStats[dirs]["zstates"][meas]=result["zstates"][meas]
                        else :
                            total = result["zmeascounts"][meas]+dirStats[dirs]["zmeascounts"][meas]
                            dirStats[dirs]["zstates"][meas]=(result["zmeascounts"][meas]*result["zstates"][meas]+dirStats[dirs]["zmeascounts"][meas]*dirStats[dirs]["zstates"][meas])/total
                            dirStats[dirs]["zmeascounts"][meas]=total

        points=[]

        for dirs in dirStats:
            if "ymeascounts" in dirStats[dirs] and "zmeascounts" in dirStats[dirs]:
                for meas in dirStats[dirs]["ymeascounts"]:
                    if meas in dirStats[dirs]["zmeascounts"]:
                        if dirStats[dirs]["ymeascounts"][meas] > threshold and dirStats[dirs]["zmeascounts"][meas] > threshold :
                            points+=[[dirStats[dirs]["ystates"][meas],dirStats[dirs]["zstates"][meas]]]

        import datetime
        
        #fig= default_visualization(points)
        #fig.savefig("test_"+str(datetime.datetime.now())+".png") # save the figure to file
        #plt.close(fig)

        return points

def argparser(toadd):
    parser = toadd.add_parser("Platonic-Fractals", help="Platonic Fractals benchmark.")
    parser.add_argument("-b", "--body", type=int, help="The type of the Platonic boby. (default=0 -- Octahedron)", default=0)
    parser.add_argument("-e", "--strength", type=float, help="The strength of the mesurements. (default=0.93)", default=0.93)
    parser.add_argument("-t", "--num_steps", type=int, help="Number of steps of the process. (default=2)", default=2)
    parser.add_argument("-d", "--num_dirs_change", type=int, help="Number of different random measurement oritentations used. (default=42)", default=42)
    parser.add_argument("-s", "--num_shots", type=int, help="Number of shots per random orientations. (default=1024)", default=1024)
    parser.add_argument("-r", "--random_seed", type=int, help="The random seed used for generatic the random orienations (default=random)", default=random.randint(1,100000000))
    return parser

def paramparser(args):
    return {
        'body' : args.body,
        'strength' : args.strength,
        'num_steps' : args.num_steps,
        'num_dirs_change' : args.num_dirs_change,
        'num_shots' : args.num_shots,
        'random_seed' : args.random_seed
    }

def default_visualization(collated_result, params=[]):
#def visualize(self, points, figName):
    rcParams['figure.figsize'] = 7, 7

    theta = np.arange(0, 2*np.pi , 0.004)        

    fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
    plt.plot(1 * np.cos(theta), 1 * np.sin(theta),color='#14498C') #'#A3E3D9'#'#14498C'
    plt.scatter(*zip(*collated_result),color='#A3E3D9') #'#3ACC23'
    ax.set_facecolor('xkcd:black') #'xkcd:salmon'
    ax.set_xlim([-1.1,1.1])
    ax.set_ylim([-1.1,1.1])

    #fig.savefig('figName') # save the figure to file
    #plt.close(fig)
    return fig