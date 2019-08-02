#!/usr/bin/python

import sys
import random

import numpy as np
import matplotlib
matplotlib.use('Agg')

import GPy
import GPyOpt

from GPyOpt.methods import BayesianOptimization

sys.path.append("./")
from base import gem5_aladdin_interface as gem5
from base import gem5_results
from base import gem5_constants
    
_BENCHMARK = "fft_transpose"
_TARGET = gem5_constants._CONST_P1

_BDS = [{'name': 'cache_size', 'type': 'discrete', 'domain': (16384, 32768, 65536, 131072)}, 
        {'name': 'cycle_time', 'type': 'discrete', 'domain': (1, 2, 3, 4, 5)},
        {'name': 'pipelining', 'type': 'discrete', 'domain': (0, 1)},
        {'name': 'tlb_hit_latency', 'type': 'discrete', 'domain': (1, 2, 3, 4)}]

_RESULTS_FILE = "results.csv"

def write_to_file(file_name, bds, parameters=None, success=None, result=None, add_head=False, overwrite=False):
    """Writes results to a file

    Args:
        file_name: results file name
        bds: domains dictionary 
        parameters: parameters' values selected for the simulation
        success: simulation success flag
        result: target value
        add_head: flag to add headings
        overwrite: flag to overwrite file
    """

    if overwrite:
        f = open(file_name, "w")
    else:
        f = open(file_name, "a")

    # adds header for the results file
    if add_head:
        head_str = "Iteration"

        params = {}
        for bd in _BDS:
            head_str = ','.join([head_str, bd['name']])

        head_str = ','.join([head_str, 'success', _TARGET])

        f.write("{}\n".format(head_str))
    
    else:
        result_str = "0"
        for idx, _ in enumerate(_BDS):

            result_str = ','.join([result_str, "%d" % (int(parameters[0][idx]))])

        result_str = ','.join([result_str, "%d" % (success), "%f" % (result)])
        
        f.write("{}\n".format(result_str))

    f.close()

if __name__ == "__main__":
    
    # Creates an output file with a header
    write_to_file(_RESULTS_FILE, _BDS, add_head=True, overwrite=True)

    def simulator(parameters):

        # setting gem5-aladdin parameters
        params = {}
        for idx, bd in enumerate(_BDS):
            params[bd['name']] = int(parameters[0][idx])

        gem5_result = gem5.main(params, rm_sim_dir=True, bench_name=_BENCHMARK)

        
        try:
            success = 1
            result = gem5_results.get_target_value(gem5_result, _TARGET)
        except:
            success = 0
            result = 0.0
            
        write_to_file(_RESULTS_FILE, _BDS, parameters=parameters, success=success, result=result)

        print("Params: ", params, " Result: ", result)

        return result  

    optimizer = BayesianOptimization(f=simulator, 
                                        domain=_BDS,
                                        model_type='GP',
                                        acquisition_type ='EI',
                                        acquisition_jitter = 0.01,
                                        exact_feval=True,
                                        maximize=True)

    optimizer.run_optimization(max_iter=20)

    optimizer.plot_acquisition(filename = "acquisition.png")

    optimizer.plot_convergence(filename = "convergence.png")