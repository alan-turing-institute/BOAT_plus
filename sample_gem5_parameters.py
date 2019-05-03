#!/usr/bin/python
"""
A script to perform random parameter sampling for the gem5-aladdin simulator.
Based on: https://github.com/cambridge-mlg/gem5-aladdin/tree/master/bo_script
"""

import numpy as np
import itertools
from multiprocessing import Pool
import time
import sys
import copy
import json

sys.path.append("./")

from base import gem5_aladdin_interface as gem5

_AVAILABLE_PARAMS = {
    'cycle_time': range(1, 6),
    'pipelining': [0, 1],
    'enable_l2': [0, 1],
    'pipelined_dma': [0, 1],
    'tlb_entries': range(17),
    'tlb_hit_latency': range(1, 5),
    'tlb_miss_latency': range(10, 21),
    'tlb_page_size': [4096, 8192],
    'tlb_assoc': [4, 8, 16],
    'tlb_bandwidth': [1, 2],
    'tlb_max_outstanding_walks': [4, 8],
    'cache_size': [16384, 32768, 65536, 131072],
    'cache_assoc': [1, 2, 4, 8, 16],
    'cache_hit_latency': range(1, 5),
    'cache_line_sz': [16, 32, 64],
    'cache_queue_size': [32, 64, 128],
    'cache_bandwidth': range(4, 17)
}

def sampling(selected_params, samples, no_workers, results_file="results.csv"):
    """Performs sampling.

    Performs sampling over the given samples. The method utilizes a pool of
        workers approach for parallelization.

    Args:
        selected_params: labels of the selected parameters
        samples: a matrix with parameter values
        no_workers: a number of workers in the pool
        results_file:

    """

    total_samples = len(samples)

    samples_splits = []
    for i in range(total_samples):
        params = {}
        for p, v in zip(selected_params, samples[i]):
            params[p] = v

        samples_splits.append(params)

    pool = Pool(processes=no_workers)
    results = pool.imap(process_sample, samples_splits)

    result_cnt = 0
    for result in results:
        print(result)

        if result_cnt > 0:
            write_to_file(results_file, result)
        else:
            write_to_file(results_file, result, add_head=True, overwrite=True)

        result_cnt += 1

    return

def process_sample(params):
    """Processes parameters with gem5-aladdin

    """

    params_cpy = copy.copy(params)

    try:
        result = gem5.main(params)
        params_cpy.update(result)
        params_cpy.update({"success":True})
    except:
        result = {}
        params_cpy.update({"success":False})
    return params_cpy

def write_to_file(file_name, dict, add_head=False, overwrite=False):
    """Writes dictionary results to a file

    Args:
        file_name: results file
        dict: results dictionary
        add_head: flag to add headings
        overwrite: flag to overwrite
    """

    if overwrite:
        f = open(file_name, "w")
    else:
        f = open(file_name, "a")

    if add_head:
        head_str = ""

        key_cnt = 0
        for key, val in dict.items():
            if key_cnt > 0:
                head_str = "{},".format(head_str)

            head_str = "{}{}".format(head_str, key)
            key_cnt += 1

        f.write("{}\n".format(head_str))

    value_str = ""

    key_cnt = 0
    for key, val in dict.items():
        if key_cnt > 0:
            value_str = "{},".format(value_str)

        value_str = "{}{}".format(value_str, str(val))
        key_cnt += 1

    f.write("{}\n".format(value_str))

    f.close()

def prep_and_run_samples(selected_params, results_file):
    """Prepares and runs samples

    Args:
        selected_params:
        results_file:
    """

    grid = np.array(list(itertools.product(*[_AVAILABLE_PARAMS[p] for p in selected_params])))

    print("Total number of samples: {}".format(str(len(grid))))

    # random shuffle of paramters
    np.random.shuffle(grid)

    # performs random sampling
    sampling(selected_params, grid, NO_WORKERS, results_file)

if __name__ == "__main__":

    # At the moment it is impossible to run multiple gem5-aladdin instances, thus NO_WORKERS = 1
    NO_WORKERS = 1
    def_results_file = "results.csv"

    single_param_mode = True

    if single_param_mode:

        for avail_param_key in _AVAILABLE_PARAMS.keys():

            selected_params = [avail_param_key]
            results_file = avail_param_key + "_" + def_results_file

            prep_and_run_samples(selected_params, results_file)

    else:
        # TODO: this is not the correct place to list parameters
        selected_params = ['cycle_time', 'pipelining', 'pipelined_dma', 'cache_assoc']

        prep_and_run_samples(selected_params, def_results_file)


    print("Finished.")
