# coding: UTF-8

import asyncio
import os
import shlex
from typing import Optional, Set

import psutil

from benchmark.driver.base_driver import BenchDriver


class SparkGPUDriver(BenchDriver):
    _benches: Set[str] = {'GpuDSArrayMult', 'GpuEnablerExample', 'GpuEnablerCodegen', 'GpuKMeans', 'GpuKMeansBatch',
                          'GpuKMeansBatchSmall', 'SparkDSLR', 'SparkDSLRmod', 'SparkGPULR', 'perfDebug'}
    bench_name: str = 'sparkgpu'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in SparkGPUDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        children = self._async_proc_info.children(True)

        if len(children) is 0:
            return None
        else:
            return children[0]

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        cmd = '{0}/bin/run-example {1}'.format(self._bench_home, self._name)

        env = os.environ.copy()
        env['M2_HOME'] = '/home/nvidia/.m2'
        env['MAVEN_HOME'] = '/opt/apache-maven-3.5.4'
        env['PATH'] = env['MAVEN_HOME'] + '/bin/:' + env['PATH']

        return await asyncio.create_subprocess_exec(
            *shlex.split(cmd),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            env=env)