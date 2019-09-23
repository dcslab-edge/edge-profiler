#!/usr/bin/env python3
# coding: UTF-8

import csv
from collections import OrderedDict
from functools import reduce
from pathlib import Path
from statistics import mean
from typing import List, Dict

from orderedset import OrderedSet

from post_scripts.tools import WorkloadResult, read_config, read_result


def run(workspace: Path, global_cfg_path: Path):
    results: List[WorkloadResult] = read_result(workspace)
    output_path = workspace / 'output'

    if not output_path.exists():
        output_path.mkdir(parents=True)

    # idx for N-percentile latnecy
    percentiles = [0.99, 0.98, 0.95, 0.50]
    percentile_lat: Dict[str, float] = dict()
    avg_lat = None
    sorted_lat = []

    #FIXME: NEED TO FIX
    for workload_result in results:
        latency_data = workload_result.bench_output
        print(f'{workload_result.name}, latency_data: {latency_data}')
        sorted_lat: List[float] = sorted(latency_data, reverse=True)    # sorting requests in descending order
        total_reqs = len(latency_data)  # e.g., 200 for ssd_eval
        # Counting index for latency_reqs and find latency data according to the percentiles
        print(f'{workload_result.name}, sorted_lat: {sorted_lat}')
        for perc in percentiles:
            req_lat_idx = int(total_reqs*(float(1-perc)))
            k = '{}p'.format(int(perc*100))
            v = sorted_lat[req_lat_idx]
            print(f'req_lat_idx: {req_lat_idx}, sorted_lat[{req_lat_idx}]: {v}')
            percentile_lat[k] = v

        avg_lat = sum(latency_data) / total_reqs

        with (output_path / f'lat_{workload_result.name}.log').open('w') as fp:
            for perc, perc_lat in percentile_lat.items():
                ret = f'{perc} latency: {round(perc_lat, 4)}\n'
                fp.write(ret)

            fp.write(f'Avg. latency: {round(avg_lat, 4)}\n')

            for lat in sorted_lat:
                fp.write(f'{lat}\n')
