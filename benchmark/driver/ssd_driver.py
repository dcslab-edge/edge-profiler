# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil

from benchmark.driver.base_driver import BenchDriver


class SSDDriver(BenchDriver):
    """
    SSD: Single Shot MultiBox Detection (Object Detection)
    """
    _benches: Set[str] = {'a','a'}
    bench_name: str = 'ssd'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)
    model = None
    op_type = None
    pu_type = None

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in SSDDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:

        cmdline = self._async_proc_info.cmdline()
        print(f'cmdline : {cmdline}')
        try:
            if self._async_proc_info.is_running():
                exec_cmdline = cmdline[1]
                cmdline_list = exec_cmdline.split('/')
                exec_name = cmdline_list[len(cmdline_list)-1].rstrip('.py')
                model = ''
                #for word in cmdline:
                #    if word == '':

                print(f'[_find_bench_proc] self._name: {self._name}')
                print(f'[_find_bench_proc] self._async_proc_info.name(): {self._async_proc_info.name()}')
                print(f'[_find_bench_proc] self._async_proc_info.cmdline(): {self._async_proc_info.cmdline()}')
                print(f'[_find_bench_proc] exec_name: {exec_name}')


                full_exec_name = model + '-' + exec_name
                #print(f'self._name: {self._name}')
                if self._name == full_exec_name and self._async_proc_info.is_running():
                    return self._async_proc_info
        except (IndexError, UnboundLocalError) as ex:
            #print(f'{model}-{exec_name} is finished')
            #print(f'Inception v3 finished!')
            print(f'self._async_proc_info: {self._async_proc_info}')
            print(f'self._async_proc_info.is_running(): {self._async_proc_info.is_running()}')
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
        print(f'batch_size: {self._batch_size}')

        #if op_type == 'eval' and model == 'inceptionv3':
        #    model = 'inceptionv3'
        #elif op_type == 'train' and model == 'inceptionv3':
        #    model = 'inception_v3'

        if op_type == 'eval' and pu_type == 'cpu':
            cmd = f'python {self._bench_home}/ssd-eval.py --cuda FALSE'
        elif op_type == 'eval' and pu_type == 'gpu':
            cmd = f'python {self._bench_home}/eval-gpu.py --data /ssd/raw_data -a {model} -b {self._batch_size} -e'
        elif op_type == 'train' and pu_type == 'gpu':
            cmd = f'python {self._bench_home}/train-gpu.py -a {model} --lr 0.01 -b {self._batch_size} --epochs 1 /ssd/raw_data'

        return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL)
