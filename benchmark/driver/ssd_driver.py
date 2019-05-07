# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil

from benchmark.driver.base_driver import BenchDriver


class SSDDriver(BenchDriver):
    """
    SSD: Single Shot MultiBox Detection (Object Detection)
    """
    _benches: Set[str] = {'ssd-eval-vgg-cpu-small', 'ssd-eval-vgg-cpu-large', 'ssd-eval-vgg-gpu-small',
                          'ssd-eval-vgg-gpu-large', 'ssd-train-vgg-cpu', 'ssd-train-vgg-gpu'}
    bench_name: str = 'ssd'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)

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
                model = 'vgg' #FIXME: hard-coded
                pu_type = ''
                for word in cmdline_list:
                    if word == 'False':
                        pu_type = 'cpu'
                    elif word == 'True':
                        pu_type = 'gpu'
                    elif word == 'test_small':
                        data_type = 'small'
                    elif word == 'test_many':
                        data_type = 'large'
                """        
                print(f'[_find_bench_proc] self._name: {self._name}')
                print(f'[_find_bench_proc] self._async_proc_info.name(): {self._async_proc_info.name()}')
                print(f'[_find_bench_proc] self._async_proc_info.cmdline(): {self._async_proc_info.cmdline()}')
                print(f'[_find_bench_proc] exec_name: {exec_name}')
                """

                #full_exec_name = model + '-' + exec_name
                full_exec_name = exec_name + '-' + model + '-' + pu_type + '-' + data_type
                print(f'self._name: {self._name}')
                print(f'full_exec_name: {full_exec_name}')
                if self._name == full_exec_name and self._async_proc_info.is_running():
                    return self._async_proc_info
        except (IndexError, UnboundLocalError) as ex:
            print(f'self._async_proc_info: {self._async_proc_info}')
            print(f'self._async_proc_info.is_running(): {self._async_proc_info.is_running()}')
            return self._async_proc_info

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        bench_name = self._name
        splitted_name = bench_name.split('-')
        #print(f'splitted_name: {splitted_name}')
        op_type = splitted_name[1]  # op_type : eval or train
        model = splitted_name[2]    # model : alex or vgg (default: vgg)
        pu_type = splitted_name[3]  # pu_type : processing unit (e.g., cpu or gpu)
        if op_type == "eval":
            data_type = splitted_name[4]    # data_type : input data type (e.g., test_small or test_many)
            if "small" in data_type:
                data_type = "test_small"
            elif "large" in data_type:
                data_type = "test_many"
        else:
            data_type = None
        #print(f'splitted_name: {splitted_name}')
        print(f'model: {model}')
        print(f'op_type: {op_type}')
        print(f'pu_type: {pu_type}')
        print(f'data_type: {data_type}')
        print(f'batch_size: {self._batch_size}')

        #if op_type == 'eval' and model == 'inceptionv3':
        #    model = 'inceptionv3'
        #elif op_type == 'train' and model == 'inceptionv3':
        #    model = 'inception_v3'

        if op_type == 'eval' and pu_type == 'cpu':
            cmd = f'python {self._bench_home}/ssd-eval.py --cuda False --set_type {data_type}'
        elif op_type == 'eval' and pu_type == 'gpu':
            cmd = f'python {self._bench_home}/ssd-eval.py --cuda True --set_type {data_type}'
        elif op_type == 'train' and pu_type == 'cpu':
            cmd = f'python {self._bench_home}/ssd-train.py --cuda False --batch_size 2'
        elif op_type == 'train' and pu_type == 'gpu':
            cmd = f'python {self._bench_home}/ssd-train.py --cuda True --batch_size 2'

        return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL)
