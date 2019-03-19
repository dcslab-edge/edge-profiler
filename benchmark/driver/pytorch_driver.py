# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil

from benchmark.driver.base_driver import BenchDriver


class PyTorchDriver(BenchDriver):
    _benches: Set[str] = {'alexnet-train-gpu', 'alexnet-eval-cpu', 'vgg11-train-gpu', 'vgg11-eval-cpu'}
    bench_name: str = 'pytorch'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in PyTorchDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:

        cmdline = self._async_proc_info.cmdline()
        exec_cmdline = cmdline[1]
        cmdline_list = exec_cmdline.split('/')
        exec_name = cmdline_list[len(cmdline_list)-1].rstrip('.py')
        model = ''
        for word in cmdline:
            if word == 'alexnet' or word == 'vgg11':
                model = word
                break

        """
        print(f'[_find_bench_proc] self._name: {self._name}')
        print(f'[_find_bench_proc] self._async_proc_info.name(): {self._async_proc_info.name()}')
        print(f'[_find_bench_proc] self._async_proc_info.cmdline(): {self._async_proc_info.cmdline()}')
        print(f'[_find_bench_proc] exec_name: {exec_name}')
        """
        full_exec_name = model + '-' +exec_name
        if self._name == full_exec_name and self._async_proc_info.is_running():
            return self._async_proc_info

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        bench_name = self._name
        splitted_name = bench_name.split('-')
        #print(f'splitted_name: {splitted_name}')
        model = splitted_name[0]    # model : alex or vgg
        op_type = splitted_name[1]  # op_type : eval or train
        pu_type = splitted_name[2]  # pu_type : processing unit (e.g., cpu or gpu)
        #print(f'splitted_name: {splitted_name}')
        print(f'model: {model}')
        print(f'op_type: {op_type}')
        print(f'pu_type: {pu_type}')

        if op_type == 'eval' and pu_type == 'cpu':
            cmd = f'python {self._bench_home}/eval-cpu.py --data /ssd/raw_data -a {model} -b {batch_size} -e'
        elif op_type == 'eval' and pu_type == 'gpu':
            cmd = f'python {self._bench_home}/eval-gpu.py --data /ssd/raw_data -a {model} -b 100 -e'
        elif op_type == 'train' and pu_type == 'gpu':
            cmd = f'python {self._bench_home}/train-gpu.py -a {model} --lr 0.01 -b 160 --epochs 1 /ssd/raw_data'

        return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL)
