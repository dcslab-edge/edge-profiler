# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil
from logging import Logger
from benchmark.driver.base_driver import BenchDriver


class TailDriver(BenchDriver):
    
    _benches: Set[str] = {'tail-imgdnn','tail-masstree','tail-silo','tail-sphinx','tail-xapian','tail-moses','tail-shore','tail-specjbb'}
    bench_name: str = 'tail'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in TailDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:

        cmdline = self._async_proc_info.cmdline()
        print("===========================")
        print(f'cmdline : {cmdline}')
        try:
            if self._async_proc_info.is_running():
                exec_cmdline = cmdline[1]
                cmdline_list = exec_cmdline.split('/')
                #exec_name = cmdline_list[len(cmdline_list)-1].rstrip('.py')
                exec_name = cmdline_list[len(cmdline_list)-1].rstrip('.sh')

                        
                print(f'[_find_bench_proc] self._name: {self._name}')
                print(f'[_find_bench_proc] self._async_proc_info.name(): {self._async_proc_info.name()}')
                print(f'[_find_bench_proc] self._async_proc_info.cmdline(): {self._async_proc_info.cmdline()}')
                print(f'[_find_bench_proc] exec_name: {exec_name}')
                


                full_exec_name = exec_name
                print(f'self._name: {self._name}')
                print(f'full_exec_name: {full_exec_name}')
                if self._name == full_exec_name and self._async_proc_info.is_running():
                    return self._async_proc_info
        except (IndexError, UnboundLocalError) as ex:
            print(f'self._async_proc_info: {self._async_proc_info}')
            print(f'self._async_proc_info.is_running(): {self._async_proc_info.is_running()}')
            return self._async_proc_info

    async def process_bench_output(self, bench_output_logger: Logger) -> bool:
        pass

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        bench_name = self._name
        splitted_name = bench_name.split('-')
        workload_type = splitted_name[1]  

#            cmd = f'python {self._bench_home}/ssd-train.py --cuda False --batch_size 2'
#        elif op_type == 'train' and pu_type == 'gpu':
#            cmd = f'python {self._bench_home}/ssd-train.py --cuda True --batch_size 2'


# FIXME TBENCH_RANDSEED random generate
        if workload_type == 'imgdnn':
#            print('imgdnn!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(self._bench_home)
            cmd = f'{self._bench_home}/img-dnn/run.sh'
#            cmd = 'TBENCH_WARMUPREQS=5000 TBENCH_MAXREQS=30000 TBENCH_QPS=500 TBENCH_RANDSEED=1 TBENCH_MINSLEEPNS=10000 TBENCH_MNIST_DIR=/ssd/tailbench/tailbench.inputs/img-dnn/mnist /ssd/tailbench/tailbench-v0.9/img-dnn/./img-dnn_integrated -r 1 -f /ssd/tailbench/tailbench.inputs/img-dnn/models/model.xml -n 100000000'
#            cmd = f'TBENCH_MNIST_DIR=/ssd/tailbench/tailbench.inputs/img-dnn/mnist {self._bench_home}/img-dnn/img-dnn_integrated -r 1 -f /ssd/tailbench/tailbench.inputs/img-dnn/models/model.xml -n 100000000'
        elif workload_type == 'sphinx':
            cmd = f'{self._bench_home}/sphinx/run.sh TBENCH_RANDSEED=2'
        elif workload_type == 'xapian':
            cmd = f'{self._bench_home}/xapian/run.sh TBENCH_RANDSEED=3'

        return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.PIPE)
        #return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL)
