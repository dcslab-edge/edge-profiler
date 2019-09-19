# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil
from logging import Logger
from benchmark.driver.base_driver import BenchDriver


class PyTorchDriver(BenchDriver):
    _benches: Set[str] = {'alexnet-train-gpu', 'alexnet-eval-cpu', 'alexnet-eval-gpu', 'alexnet-train-cpu',
                          'vgg11-train-gpu', 'vgg11-eval-cpu',
                          'inceptionv3-train-gpu', 'inceptionv3-eval-cpu', 'inceptionv3-eval-gpu',
                          'inceptionv3-train-cpu', 'resnet152-train-gpu', 'resnet152-eval-cpu',
                          'squeezenet1_1-eval-cpu', 'squeezenet1_1-eval-gpu', 'squeezenet1_1-train-cpu',
                          'squeezenet1_1-train-gpu'}
    bench_name: str = 'pytorch'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)
    model = None
    op_type = None
    pu_type = None

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in PyTorchDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:

        cmdline = self._async_proc_info.cmdline()
        #print(f'cmdline : {cmdline}')
        try:
            if self._async_proc_info.is_running():
                exec_cmdline = cmdline[1]
                cmdline_list = exec_cmdline.split('/')
                exec_name = cmdline_list[len(cmdline_list)-1].rstrip('.py')
                model = ''
                for word in cmdline:
                    if word == 'alexnet' or word == 'vgg11' or word == 'resnet152':
                        model = word
                    elif word == 'inception_v3' or word == 'inceptionv3':
                        model = 'inceptionv3'
                    elif word == 'squeezenet1_1':
                        model = word

                """
                print(f'[_find_bench_proc] self._name: {self._name}')
                print(f'[_find_bench_proc] self._async_proc_info.name(): {self._async_proc_info.name()}')
                print(f'[_find_bench_proc] self._async_proc_info.cmdline(): {self._async_proc_info.cmdline()}')
                print(f'[_find_bench_proc] exec_name: {exec_name}')
                """

                full_exec_name = model + '-' + exec_name
                print(f'self._name: {self._name}')
                print(f'full_exec_name: {full_exec_name}')
                if self._name == full_exec_name and self._async_proc_info.is_running():
                    return self._async_proc_info
        except (IndexError, UnboundLocalError) as ex:
            #print(f'{model}-{exec_name} is finished')
            print(f'Inception v3 finished!')
            print(f'self._async_proc_info: {self._async_proc_info}')
            print(f'self._async_proc_info.is_running(): {self._async_proc_info.is_running()}')
            return self._async_proc_info

    async def process_bench_output(self, bench_output_logger: Logger) -> bool:
        pass

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

        if op_type == 'eval' and model == 'inceptionv3':
            model = 'inception_v3'
        elif op_type == 'train' and model == 'inceptionv3':
            model = 'inception_v3'

        if op_type == 'eval' and pu_type == 'cpu':
            #cmd = f'python {self._bench_home}/eval-cpu.py --data /ssd/raw_data -a {model} -b {self._batch_size} -e'
            cmd = f'python {self._bench_home}/eval-cpu.py /ssd/raw_data -a {model} -b {self._batch_size} -e --pretrained'
        elif op_type == 'eval' and pu_type == 'gpu':
            #cmd = f'python {self._bench_home}/eval-gpu.py --data /ssd/raw_data -a {model} -b {self._batch_size} -e'
            cmd = f'python {self._bench_home}/eval-gpu.py /ssd/raw_data -a {model} -b {self._batch_size} -e --pretrained'
        elif op_type == 'train' and pu_type == 'cpu':
            cmd = f'python {self._bench_home}/train-cpu.py -a {model} --lr 0.01 -b {self._batch_size} --epochs 1 /ssd/raw_data'
        elif op_type == 'train' and pu_type == 'gpu':
            cmd = f'python {self._bench_home}/train-gpu.py -a {model} --lr 0.01 -b {self._batch_size} --epochs 1 /ssd/raw_data'

        return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL)
