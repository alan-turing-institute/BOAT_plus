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
import random

sys.path.append("./")

from base import gem5_aladdin_interface as gem5

_CONST_TLB_ASSOC = 'tlb_assoc'
_CONST_TLB_ENTRIES = 'tlb_entries'

_AVAILABLE_PARAMS = {
    ############################################################################
    # Core Aladdin parameters.
    'cycle_time': range(1, 6),
    'pipelining': [0, 1],
    #
    # Parameters that are not being used
    #   copied from alladin to show the default values being used
    #
    # unrolling = IntParam("unrolling", 1)
    # partition_factor = IntParam("partition_factor", 1)
    # partition_type = StrParam("partition_type", CYCLIC,
    #                             valid_opts=[COMPLETE, CYCLIC, BLOCK])
    # Parameters that are not being used
    # memory_type = StrParam("memory_type", SPAD, valid_opts=[SPAD, CACHE])
    #
    ############################################################################
    # Cache memory system parameters.
    ############################################################################
    'cache_size': [16384, 32768, 65536, 131072], # in bytes
    'cache_assoc': [1, 2, 4, 8, 16],
    'cache_hit_latency': range(1, 5),
    'cache_line_sz': [16, 32, 64],
    'cache_queue_size': [32, 64, 128],
    'cache_bandwidth': range(4, 17),
    'tlb_hit_latency': range(1, 5),
    'tlb_miss_latency': range(10, 21),
    'tlb_page_size': [4096, 8192],               # in bytes
    'tlb_entries': range(17),                    # number of tlb entries - it is in a form of multiples of tlb_assoc
    'tlb_max_outstanding_walks': [4, 8],
    'tlb_assoc': [4, 8, 16],                     # tlb associativity
    'tlb_bandwidth': [1, 2],
    #
    # Parameters that are not being used
    #   copied from alladin to show the default values being used
    #
    # l2cache_size = IntParam("l2cache_size", 128*1024, format_func=intToShortSize)
    # perfect_l1 = IntParam("perfect_l1", 0)
    # perfect_bus = IntParam("perfect_bus", 0)
    # enable_l2 = IntParam("enable_l2", 0)
    ############################################################################
    # DMA settings.
    ############################################################################
    'pipelined_dma': [0, 1]
    #
    # Parameters that are not being used
    #   copied from alladin to show the default values being used
    #
    # dma_setup_overhead = IntParam("dma_setup_overhead", 30)
    # max_dma_requests = IntParam("max_dma_requests", 40)
    # dma_chunk_size = IntParam("dma_chunk_size", 64)
    # ready_mode = IntParam("ready_mode", 0)
    # dma_multi_channel = IntParam("dma_multi_channel", 0)
    # ignore_cache_flush = IntParam("ignore_cache_flush", 0)
    # invalidate_on_dma_store = BoolParam("invalidate_on_dma_store", True)
}

_RESULTS_PARAMS = ['success','cycle', 'power', 'area']

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

    # check if _CONST_TLB_ASSOC and _CONST_TLB_ENTRIES are listed
    try:
        tlb_assoc_idx = selected_params.index(_CONST_TLB_ASSOC)
        tlb_entries_idx = selected_params.index(_CONST_TLB_ENTRIES)
        tlb_entries_calc = True
    except:
        tlb_assoc_idx = -1
        tlb_entries_idx = -1
        tlb_entries_calc = False

    total_samples = len(samples)

    samples_splits = []
    for i in range(total_samples):
        params = {}

        for p, v in zip(selected_params, samples[i]):
            params[p] = v

        # if _CONST_TLB_ENTRIES and _CONST_TLB_ASSOC are listed as simulated
        #    parameters recalculate _CONST_TLB_ENTRIES
        if tlb_entries_calc:
            params[_CONST_TLB_ENTRIES] = params[_CONST_TLB_ENTRIES] * params[_CONST_TLB_ASSOC]

        samples_splits.append(params)

    pool = Pool(processes=no_workers)
    results = pool.imap(process_sample, samples_splits)

    result_cnt = 0
    for result in results:

        if result_cnt > 0:
            write_to_file(results_file, result, selected_params)
        else:
            write_to_file(results_file, result, selected_params, add_head=True, overwrite=True)

        result_cnt += 1

        print(result)

    return

def process_sample(params):
    """Processes parameters with gem5-aladdin

    """

    params_cpy = copy.copy(params)

    try:
        result = {}
        params_cpy.update({"success":False})

        # setting result values as false
        for res_param in _RESULTS_PARAMS:
            params_cpy.update({res_param:False})


        # result = gem5.main(params, rm_sim_dir=True)
        # params_cpy.update(result)
        # params_cpy.update({"success":True})

    except:
        result = {}
        params_cpy.update({"success":False})

        # setting result values as false
        for res_param in _RESULTS_PARAMS:
            params_cpy.update({res_param:False})

    return params_cpy

def write_to_file(file_name, res_dict, selected_params, add_head=False, overwrite=False):
    """Writes dictionary results to a file

    Args:
        file_name: results file
        res_dict: results dictionary
        selected_params: list of sampled parameters
        add_head: flag to add headings
        overwrite: flag to overwrite
    """

    if overwrite:
        f = open(file_name, "w")
    else:
        f = open(file_name, "a")

    # adds header for the results file
    if add_head:
        head_str = ','.join([','.join(selected_params), ','.join(_RESULTS_PARAMS)])

        f.write("{}\n".format(head_str))

    # parameters' values + simulation results
    values_str = ','.join([list_dict_values(res_dict, selected_params),
        list_dict_values(res_dict, _RESULTS_PARAMS)])

    f.write("{}\n".format(values_str))

    f.close()

def list_dict_values(res_dict, keyword_list):
    """Forms a string listing values from a dictionary with respect to a keyword list

    Args:
        res_dict: results dictionary
        keyword_list: a list of keywords

    Returns:
        value_str: a string listing values from a dictionary
    """

    value_str = ""

    key_cnt = 0
    for keyword in keyword_list:

        val = res_dict[keyword]

        if key_cnt > 0:
            value_str = "{},".format(value_str)

        value_str = "{}{}".format(value_str, str(val))
        key_cnt += 1

    return value_str

def prep_and_run_samples(selected_params, results_file, randomise=True,
    no_of_random_samples=None, unique_saples=False):

    """Prepares and runs samples

    Args:
        selected_params:
        results_file:
        randomise: a flag to randomise grid lines
        no_of_random_samples: a fixed number of samples to be evaluated
        unique_saples: enforce uniqueness of samples
    """

    if no_of_random_samples is not None:

        no_of_params = len(selected_params)

        grid = np.empty((no_of_random_samples, no_of_params), dtype=np.int32)

        for i in range(no_of_random_samples):
            for j in range(no_of_params):
                param = _AVAILABLE_PARAMS[selected_params[j]]

                grid[i][j] = random.choice(param)

        if unique_saples:
            grid = np.unique(grid, axis=0)

    else:
        grid = np.array(list(itertools.product(*[_AVAILABLE_PARAMS[p] for p in selected_params])))

        if randomise:
            # random shuffle of paramters
            np.random.shuffle(grid)

    print("Total number of samples: {}".format(str(len(grid))))

    # performs random sampling
    sampling(selected_params, grid, NO_WORKERS, results_file)

def list_parameters(values_list):

    key_cnt = 0

    for key, val in dict.items():
        if key_cnt > 0:
            head_str = "{},".format(head_str)

        head_str = "{}{}".format(head_str, key)
        key_cnt += 1

if __name__ == "__main__":

    # At the moment it is impossible to run multiple gem5-aladdin instances, thus NO_WORKERS = 1
    NO_WORKERS = 1
    def_results_file = "results.csv"
    single_param_mode = False
    no_of_random_samples = 10
    unique_saples = True

    if single_param_mode:

        for avail_param_key in _AVAILABLE_PARAMS.keys():

            selected_params = [avail_param_key]
            results_file = avail_param_key + "_" + def_results_file

            prep_and_run_samples(selected_params, results_file)

    else:
        # TODO: this is not the correct place to list parameters
        selected_params = list(_AVAILABLE_PARAMS.keys())
        #selected_params = ['cache_size', 'cache_assoc']

        prep_and_run_samples(selected_params, def_results_file,
                no_of_random_samples=no_of_random_samples, unique_saples=unique_saples)

    print("Finished.")
