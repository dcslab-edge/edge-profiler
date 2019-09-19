# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil
from logging import Logger
from benchmark.driver.base_driver import BenchDriver


class NPBDriver(BenchDriver):
    _benches: Set[str] = {'CG', 'IS', 'DC', 'EP', 'MG', 'FT', 'SP', 'BT', 'LU', 'UA'}
    bench_name: str = 'npb'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)

    # TODO: variable data size
    DATA_SET_MAP = {
        'CG': 'C',
        'IS': 'D',
        'DC': 'B',
        'EP': 'C',
        'MG': 'C',
        'FT': 'C',
        'SP': 'C',
        'BT': 'C',
        'LU': 'C',
        'UA': 'C',
    }

    @property
    def _exec_name(self) -> str:
        return f'{self._name.lower()}.{NPBDriver.DATA_SET_MAP[self._name]}.x'

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in NPBDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        exec_name = self._exec_name

        if self._async_proc_info.name() == exec_name and self._async_proc_info.is_running():
            return self._async_proc_info

        return None

    async def process_bench_output(self, bench_output_logger: Logger) -> bool:
        pass

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        exec_name = self._exec_name

        cmd = '{0}/bin/{1}'.format(self._bench_home, exec_name)
        env = {'OMP_NUM_THREADS': str(self._num_threads)}

        return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL, env=env)
