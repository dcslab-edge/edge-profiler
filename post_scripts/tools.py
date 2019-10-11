# coding: UTF-8

import csv
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from benchmark_launcher import parse_launcher_cfg, parse_perf_cfg, parse_rabbit_mq_cfg, parse_workload_cfg
from containers.bench_config import BenchConfig
from containers.launcher_config import LauncherConfig
from containers.perf_config import PerfConfig
from containers.rabbit_mq_config import RabbitMQConfig


class WorkloadResult:
    def __init__(self, name: str, runtime: float, metrics: OrderedDict, bench_output: List[float]):
        self._name: str = name
        self._runtime: float = runtime
        self._metrics: OrderedDict = metrics
        self._bench_output: List[float] = bench_output

    @property
    def runtime(self):
        return self._runtime

    @property
    def metrics(self):
        return self._metrics

    @property
    def name(self):
        return self._name

    @property
    def bench_output(self):
        return self._bench_output


def read_result(workspace: Path) -> List[WorkloadResult]:
    result_file = workspace / 'result.json'
    metric_path = workspace / 'perf'
    bench_output_path = workspace / 'bench_output'

    if not result_file.is_file() or not metric_path.is_dir() or not bench_output_path.is_dir():
        raise ValueError('run benchmark_launcher.py first!')

    with result_file.open() as result_fp:
        result: Dict[str, Any] = json.load(result_fp)

    ret: List[WorkloadResult] = list()

    for workload_name, runtime in result['runtime'].items():  # type: str, float
        metric_map = OrderedDict()
        bench_output_results = []

        with (metric_path / f'{workload_name}.csv').open() as metric_fp:
            reader = csv.DictReader(metric_fp)

            for field in reader.fieldnames:
                metric_map[field] = []

            for row in reader:
                for k, v in row.items():  # type: str, str
                    metric_map[k].append(float(v))

        with (bench_output_path / f'{workload_name}.log').open() as bench_output_fp:
            num_line = 1
            lat_flag = False
            for line in bench_output_fp.readlines():
                #line = bench_output_fp.readline().rstrip('\n')
                if line == "":
                    break
                if num_line >= 2:
                    if "times" in line or 'ssd' in workload_name:
                        lat_flag = True
                    elif ',' in line and lat_flag: #
                        # FIXME: hard-coded for tailbench
                        line = line.rstrip('\n').split(",")
                        bench_output_results.append((float(line[2])))
                    else:   # ssd case
                        if lat_flag:
                            bench_output_results.append(float(line))
                num_line += 1
        #print(bench_output_results)
        ret.append(WorkloadResult(workload_name, runtime, metric_map, bench_output_results))

    return ret


def read_config(workspace: Path, global_cfg_path: Path) -> \
        Tuple[Tuple[BenchConfig, ...], PerfConfig, RabbitMQConfig, LauncherConfig]:
    local_cfg_path = workspace / 'config.json'

    if not local_cfg_path.is_file() or not global_cfg_path.is_file():
        raise ValueError('run benchmark_launcher.py first!')

    with local_cfg_path.open() as local_fp, \
            global_cfg_path.open() as global_fp:
        local_cfg: Dict[str, Any] = json.load(local_fp)
        global_cfg: Dict[str, Any] = json.load(global_fp)

    return \
        parse_workload_cfg(local_cfg['workloads']), \
        parse_perf_cfg(global_cfg['perf'], local_cfg.get('perf', {'extra_events': []})), \
        parse_rabbit_mq_cfg(global_cfg['rabbitMQ']), \
        parse_launcher_cfg(local_cfg['launcher'])
