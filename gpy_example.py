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
    
_BENCHMARK = "aes_aes"
_TARGET = gem5_constants._CONST_P1

from numpy.random import seed
seed(123)


_GEM5_DICT_CACHE_SIZE = {0:16384, 1:32768, 2:65536, 3:131072}
_GEM5_DICT_CACHE_ASSOC = {0:1, 1:2, 2:4, 3:8, 4:16}
_GEM5_DICT_CACHE_LINE_SZ = {0:16, 1:32, 2:64}

# _GEM5_DICT_PIPELINING = {0:0, 1:1}
# _GEM5_DICT_TLB_BANDWIDTH = {0:1, 1:2}
# _GEM5_DICT_CACHE_HIT_LATENCY = {0:1, 1:2, 2:3, 3:4}
# _GEM5_DICT_CYCLE_TIME = {0:1, 1:2, 2:3, 3:4, 4:5}
# _GEM5_DICT_TLB_HIT_LATENCY = {0:1, 1:2, 2:3, 3:4}


    # {'name': 'pipelining', 'type': 'categorical', 'domain': tuple(_GEM5_DICT_PIPELINING.keys())},
    # {'name': 'tlb_bandwidth', 'type': 'categorical', 'domain': tuple(_GEM5_DICT_TLB_BANDWIDTH.keys())},
    # {'name': 'cache_hit_latency', 'type': 'categorical', 'domain': tuple(_GEM5_DICT_CACHE_HIT_LATENCY.keys())}, 
    # {'name': 'cycle_time', 'type': 'categorical', 'domain': tuple(_GEM5_DICT_CYCLE_TIME.keys())},
    # {'name': 'tlb_hit_latency', 'type': 'categorical', 'domain': tuple(_GEM5_DICT_TLB_HIT_LATENCY.keys())}

_BDS = [
    {'name': 'cache_size', 'type': 'categorical', 'domain': tuple(_GEM5_DICT_CACHE_SIZE.keys())}, 
    {'name': 'cache_assoc', 'type': 'categorical', 'domain': tuple(_GEM5_DICT_CACHE_ASSOC.keys())}, 
    {'name': 'cache_line_sz', 'type': 'categorical', 'domain': tuple(_GEM5_DICT_CACHE_LINE_SZ.keys())}, 
    {'name': 'pipelining', 'type': 'discrete', 'domain': (0, 1)},
    {'name': 'tlb_bandwidth', 'type': 'discrete', 'domain': (1, 2)},
    {'name': 'cache_hit_latency', 'type': 'discrete', 'domain': (1, 2, 3, 4)}, 
    {'name': 'cycle_time', 'type': 'discrete', 'domain': (1, 2, 3, 4, 5)},
    {'name': 'tlb_hit_latency', 'type': 'discrete', 'domain': (1, 2, 3, 4)}
    ]

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
            param_name = bd['name']
            if param_name == "cache_size":
                value = _GEM5_DICT_CACHE_SIZE[int(parameters[0][idx])]
            elif param_name == "cache_assoc":
                value = _GEM5_DICT_CACHE_ASSOC[int(parameters[0][idx])]
            elif param_name == "cache_line_sz":
                value = _GEM5_DICT_CACHE_LINE_SZ[int(parameters[0][idx])]
            # elif param_name == "pipelining":
            #     value = _GEM5_DICT_PIPELINING[int(parameters[0][idx])]
            # elif param_name == "tlb_bandwidth":
            #     value = _GEM5_DICT_TLB_BANDWIDTH[int(parameters[0][idx])]
            # elif param_name == "cache_hit_latency":
            #     value = _GEM5_DICT_CACHE_HIT_LATENCY[int(parameters[0][idx])]
            # elif param_name == "cycle_time":
            #     value = _GEM5_DICT_CYCLE_TIME[int(parameters[0][idx])]
            # elif param_name == "tlb_hit_latency":
            #     value = _GEM5_DICT_TLB_HIT_LATENCY[int(parameters[0][idx])]
            else:
                value = int(parameters[0][idx])
            
            params[param_name] = value
        
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
                                        exact_feval=True,
                                        maximize=True)

    optimizer.run_optimization(max_iter=50, verbosity=True, eps=-1)

    optimizer.plot_acquisition(filename = "acquisition.png")

    optimizer.plot_convergence(filename = "convergence.png")