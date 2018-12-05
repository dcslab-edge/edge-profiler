# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil

from benchmark.driver.base_driver import BenchDriver


class RodiniaDriver(BenchDriver):
    _benches: Set[str] = {'nn', 'kmeans', 'cfd', 'particlefilter', 'bfs'}
    bench_name: str = 'rodinia'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in RodiniaDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._name == 'cfd':
            exec_name = 'euler3d_cpu'
        elif self._name == 'particlefilter':
            exec_name = 'particle_filter'
        else:
            exec_name = self._name

        for process in self._async_proc_info.children(recursive=True):  # type: psutil.Process
            if process.name() == exec_name and process.is_running():
                return process

        return None

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        cmd = '{0}/openmp/{1}/run' \
            .format(self._bench_home, self._name)
        env = {
            'OMP_NUM_THREADS': str(self._num_threads),
            'GOMP_CPU_AFFINITY': str(self._binding_cores)
        }

        return await self._cgroup.exec_command(cmd, env=env,
                                               stdout=asyncio.subprocess.DEVNULL,
                                               stderr=asyncio.subprocess.DEVNULL)
