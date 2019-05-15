#!/usr/bin/python
"""
A module to prepare header files for the simulated accelerators,
    execute them and retrieve the results.
"""

import argparse
import os
import re
import uuid

# A list of available accelerator parameters
_AVAILABLE_PARAMS = [
    # Core
    'cycle_time',
    'pipelining',
    'unrolling',
    'partition_factor',
    'partition_type'
    'memory_type',
    # Cache
    'cache_size',
    'cache_assoc',
    'cache_hit_latency',
    'cache_line_sz',
    'cache_queue_size',
    'cache_bandwith',
    'tlb_hit_latency',
    'tlb_miss_latency',
    'tlb_page_size',
    'tlb_entries',
    'tlb_max_outstanding_walks',
    'tlb_assoc',
    'tlb_bandwidth',
    'l2cache_size',
    'perfect_l1'
    'perfect_bus'
    'enable_l2',
    # DMA
    'pipelined_dma',
    'dma_setup_overhead',
    'max_dma_requests',
    'dma_chunk_size',
    'ready_mode',
    'dma_multi_channel',
    'ignore_cache_flush',
    'invalidate_on_dma_store'
]

# get the paths to aladdin, gem5 and other submodules
_GEM5_PATH = os.path.abspath(os.path.join(os.environ['ALADDIN_HOME'], '..', '..'))

_GEM5_BENCH_DIR_NAME = 'benchmarks'
_GEM5_SWEEPS_DIR_NAME = 'sweeps'
_GEM5_SWEEPS_DESIGN_PY = 'generate_design_sweeps.py'

_GEM5_SWEEPS_PATH = os.path.join(_GEM5_PATH, _GEM5_SWEEPS_DIR_NAME)
_GEM5_SWEEPS_DESIGN_PY_PATH = os.path.join(_GEM5_SWEEPS_PATH, _GEM5_SWEEPS_DESIGN_PY)
_GEM5_SWEEPS_BENCH_PATH = os.path.join(_GEM5_SWEEPS_PATH, _GEM5_BENCH_DIR_NAME)

_SIM_SWEEP_NAME = "{}{}".format("sim_", str(uuid.uuid4())[:12])
_SIM_OUTPUT_DIR = os.path.join(_GEM5_SWEEPS_PATH, _SIM_SWEEP_NAME)

# Choosing the benchmark
_DEFAULT_BENCH = "fft_transpose"
_BENCH_OUT_PARTIAL_PATH = "0"
_BENCH_OUT_FILE = "outputs/stdout"

# Default constants
_DEFAULT_RESULT_FILE = "gem5_sim_res.txt"

def create_header_from_template(params, header_path, sim_output_dir, template_path='template.xe'):
    """Prepares a simulator input file based on a template.

    Reads in a provided template file, sets output directory and parameters for the accelerator,
        saves the resulting configuration as a header file in to header_path.

    Args:
        params: a dictionary with the parameters of the simulated accelerator
        header_name: full path where the simulator header
        sim_output_dir: full path to the directory where the results from the simulator should
            be saved
        template_path: full path to the template file

    """

    # Read in the template file
    with open(template_path, 'r') as src_file:
        out_src = src_file.read()

    # Setting the output directory for the simulator results
    out_src = out_src.replace('$OUTPUT_DIR', '{0}'.format(sim_output_dir))

    # Check which parameters match with available parameters and add those values to the header file
    params_src = ''
    for key in set(_AVAILABLE_PARAMS).intersection(params):
        params_src = '%s set %s %s\n' % (params_src, key, params[key])

    out_src = out_src.replace('# Insert here\n', params_src)

    # Writing the new header file
    with open(header_path, 'w') as ouput_file:
        ouput_file.write(out_src)

def collect_result(results_file_path):
    """Collects results from a simululation run

    Args:
        results_file_path: full path to the simulation results file

    Returns:
        results: a dict mapping simulation results
    """

    results = {}

    cycle = [re.findall(r'Cycle : (.*) cycles', line) for line in open(results_file_path)]
    cycle = [c for l in cycle for c in l]
    cycle = int(cycle[0])

    results['cycle'] = cycle

    power = [re.findall(r'Avg Power: (.*) mW', line) for line in open(results_file_path)]
    power = [p for l in power for p in l]

    power = float(power[0])

    results['power'] = power

    area = [re.findall(r'Total Area: (.*) uM', line) for line in open(results_file_path)]
    area = [a for l in area for a in l]

    area = float(area[0])

    results['area'] = area

    return results

def main(sim_params, sim_output_dir=_SIM_OUTPUT_DIR, bench_name=_DEFAULT_BENCH):
    """Collects results from a simululation run

    Args:
        sim_params: parameters for the simulator
        sim_output_dir: directory to save simulator's production runs
        bench_name: benchmark to be run with the simulator

    Returns:
        results: a dict mapping simulation results. For example:
          results = {'area': 1094960.0, 'power': 67.5946, 'cycle': 65029}
    """

    # template file
    header_file_name = "{}{}".format("t_", str(uuid.uuid4()))
    header_file_path = os.path.join(_GEM5_SWEEPS_BENCH_PATH, header_file_name)

    # Preparing input input file for the simulator
    create_header_from_template(sim_params, header_file_path, sim_output_dir)

    # Generating design sweeps using the script provided with gem5
    # It seems that gem5 generate_design_sweeps.py needs to be executed in the `gem5-aladdin/sweeps` directory.
    # TODO: check above
    _CWD = os.getcwd()
    os.chdir(_GEM5_SWEEPS_PATH)

    # Preparating the benchmarks
    # TODO: (currently preparaes all the benchmarks, do we need only specific one, e.g. fft_transpose)
    # TODO: python2 needs to be python?
    os.system('python2 %s %s' % (_GEM5_SWEEPS_DESIGN_PY_PATH,
                                 os.path.join(_GEM5_BENCH_DIR_NAME, header_file_name)))

    os.chdir(_CWD)

    # removing the temporary header file
    if os.path.exists(header_file_path):
        os.remove(header_file_path)

    # Running the bechmark with the simulator
    bench_path = os.path.join(sim_output_dir, bench_name, _BENCH_OUT_PARTIAL_PATH)
    os.chdir(bench_path)

    # Performing the benchmark
    os.system('sh run.sh')

    os.chdir(_CWD)

    # Collecting the results from the simululation run
    results_file_path = os.path.join(bench_path, _BENCH_OUT_FILE)

    results = collect_result(results_file_path)

    return results

if __name__ == "__main__":

    # Setting up the argument parser
    parser = argparse.ArgumentParser(description='Run gem5-alladin benchmark')
    parser.add_argument('sim_params', type=str,
                        help='Parameters for the simulator as string representation of a Python dict')
    parser.add_argument('results_key', type=str, choices=['cycle', 'power', 'area'],
                        help='Key value of a targeted accelerator specification')
    parser.add_argument('--results_file', type=str, default=_DEFAULT_RESULT_FILE,
                        help='Filename to save the results.')

    args = parser.parse_args()

    _PARAMS = eval(args.sim_params)

    # execute the benchmark with the simulator. If it fails at somepoint
    #  return an empty result.
    try:
        results = main(_PARAMS)
    except:
        results = {}

    # saving the results that BOAT could read in
    with open(_DEFAULT_RESULT_FILE, "w") as res_file:
        if not results:
            res_file.write(str(0.0))
        else:
            res_file.write(str(results[args.results_key]))

    # TODO: do we need to clean up _SIM_OUTPUT_DIR ?
