# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil
from logging import Logger
from benchmark.driver.base_driver import BenchDriver


class ITailDriver(BenchDriver):
    
    _benches: Set[str] = {'itail-img-dnn', 'itail-masstree', 'itail-silo', 'itail-sphinx',
                          'itail-xapian', 'itail-moses', 'itail-shore', 'itail-specjbb'}
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
                print(f'[_find_bench_proc] process: {process}')
                return process

        return None

    async def process_bench_output(self, bench_output_logger: Logger) -> bool:
        ignore_flag = False
        """
        bench_output_logger.info(f'self._bench_driver.is_running: {self._bench_driver.is_running}')
        bench_output_logger.info(f'self._bench_driver.async_proc.returncode: '
                                 f'{self._bench_driver.async_proc.returncode}')
        bench_output_logger.info(f'make_output: '
                                 f'{make_output}')
        """
        raw_line = await self.async_proc.stdout.readline()
        line = raw_line.decode().strip().rstrip('\n')
        # bench_output_logger.info(f'{line}')
        #ex) im_detect: 26/100 0.172s
        #ex) timer: 0.333 sec.
        # FIXME: hard-coded for ssd driver

        if "latencies:" in line:
            # Eval: latency per image
            #splitted = line.split(', ')
            #latency_seconds = splitted
            latency_seconds = line.lstrip("latencies: ")
            bench_output_logger.info(latency_seconds)
            ignore_flag = False
        else:
            ignore_flag = True
            if line == 'end of tail bench':
                return True

        #if not ignore_flag:
        #    bench_output_logger.info(latency_seconds)

        return False

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        bench_name = self._name
        print(f'bench_name: {bench_name}')
        bench_name = bench_name.lstrip('itail').lstrip('-')
        print(f'bench_name: {bench_name}')

        # FIXME: TBENCH_RANDSEED random generate
        if bench_name == 'img-dnn':
            print(self._bench_home)
            cmd = f'{self._bench_home}/{bench_name}/run-integrated.sh'
            # cmd = 'TBENCH_WARMUPREQS=5000 TBENCH_MAXREQS=30000 TBENCH_QPS=500 TBENCH_RANDSEED=1 TBENCH_MINSLEEPNS=10000 TBENCH_MNIST_DIR=/ssd/tailbench/tailbench.inputs/img-dnn/mnist /ssd/tailbench/tailbench-v0.9/img-dnn/./img-dnn_integrated -r 1 -f /ssd/tailbench/tailbench.inputs/img-dnn/models/model.xml -n 100000000'
            # cmd = f'TBENCH_MNIST_DIR=/ssd/tailbench/tailbench.inputs/img-dnn/mnist {self._bench_home}/img-dnn/img-dnn_integrated -r 1 -f /ssd/tailbench/tailbench.inputs/img-dnn/models/model.xml -n 100000000'
        elif bench_name == 'sphinx':
            cmd = f'{self._bench_home}/{bench_name}/run.sh TBENCH_RANDSEED=2'
        elif bench_name == 'xapian':
            cmd = f'{self._bench_home}/{bench_name}/run.sh TBENCH_RANDSEED=3'

        ret = await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.PIPE)
        return ret
        #return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.PIPE)
        # return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL)
