# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil

from benchmark.driver.base_driver import BenchDriver


class ITailDriver(BenchDriver):
    
    _benches: Set[str] = {'tail-img-dnn', 'tail-masstree', 'tail-silo', 'tail-sphinx',
                          'tail-xapian', 'tail-moses', 'tail-shore', 'tail-specjbb'}
    bench_name: str = 'tail'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in ITailDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        bench_name = self._name
        exec_name = bench_name.lstrip('tail').lstrip('-') + '_integrated'
        print(f'[_find_bench_proc] bench_name: {bench_name}')
        print(f'[_find_bench_proc] exec_name: {exec_name}')

        for process in self._async_proc_info.children(recursive=True):
            print(f'[_find_bench_proc] process.name(): {process.name()}')
            if process.name() == exec_name and process.is_running():
                return process

        return None
    # def _find_bench_proc2(self) -> Optional[psutil.Process]:
    #
    #     try:
    #         if self._async_proc_info.is_running():
    #
    #             process = self._async_proc_info.children(recursive=True)
    #             # print(f'[_find_bench_proc] self._name: {self._name}')
    #             # print(f'[_find_bench_proc] self._async_proc_info.name(): {self._async_proc_info.name()}')
    #             # print(f'[_find_bench_proc] self._async_proc_info.cmdline(): {self._async_proc_info.cmdline()}')
    #             # print(f'[_find_bench_proc] exec_name: {exec_name}')
    #
    #             if self._name == process.name() and process.is_running():
    #                 return process
    #
    #     except (IndexError, UnboundLocalError) as ex:
    #         print(f'self._async_proc_info: {self._async_proc_info}')
    #         print(f'self._async_proc_info.is_running(): {self._async_proc_info.is_running()}')
    #         return self._async_proc_info

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        bench_name = self._name
        #splitted_name = bench_name.split('-')
        #workload_type = splitted_name[1]
        print(f'bench_name: {bench_name}')
        bench_name = bench_name.lstrip('tail').lstrip('-')
        print(f'bench_name: {bench_name}')


        # FIXME: TBENCH_RANDSEED random generate
        if bench_name == 'img-dnn':
        # print('imgdnn!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(self._bench_home)
            cmd = f'{self._bench_home}/{bench_name}/run-integrated.sh'
            # cmd = 'TBENCH_WARMUPREQS=5000 TBENCH_MAXREQS=30000 TBENCH_QPS=500 TBENCH_RANDSEED=1 TBENCH_MINSLEEPNS=10000 TBENCH_MNIST_DIR=/ssd/tailbench/tailbench.inputs/img-dnn/mnist /ssd/tailbench/tailbench-v0.9/img-dnn/./img-dnn_integrated -r 1 -f /ssd/tailbench/tailbench.inputs/img-dnn/models/model.xml -n 100000000'
            # cmd = f'TBENCH_MNIST_DIR=/ssd/tailbench/tailbench.inputs/img-dnn/mnist {self._bench_home}/img-dnn/img-dnn_integrated -r 1 -f /ssd/tailbench/tailbench.inputs/img-dnn/models/model.xml -n 100000000'
        elif bench_name == 'sphinx':
            cmd = f'{self._bench_home}/{bench_name}/run.sh TBENCH_RANDSEED=2'
        elif bench_name == 'xapian':
            cmd = f'{self._bench_home}/{bench_name}/run.sh TBENCH_RANDSEED=3'

        return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.PIPE)
        # return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL)
