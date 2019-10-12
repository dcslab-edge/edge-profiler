# coding: UTF-8

import asyncio
import asyncssh
from typing import Optional, Set, Dict

import psutil
import logging
from benchmark.driver.base_driver import BenchDriver
import time


class NTailDriver(BenchDriver):
    
    _benches: Set[str] = {'ntail-img-dnn', 'ntail-masstree', 'ntail-silo', 'ntail-sphinx',
                          'ntail-xapian', 'ntail-moses', 'ntail-shore', 'ntail-specjbb'}
    bench_name: str = 'tail'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)
    workload_name = None
    server_proc = None

    reader = None    # session used for receiving results by using AsyncSSH

    # FIXME: hard-coded
    server_base_path = '/ssd/tailbench/tailbench-v0.9'
    client_base_path = '/ssd2/tailbench/tailbench'
    server_input_path = '/ssd/tailbench/tailbench.inputs'
    client_input_path = '/ssd2/tailbench/tailbench.inputs'
    # TODO: DATA_MAPS currently works on img-dnn only
    SERVER_DATA_MAPS = {
        "img-dnn": "models/model.xml",
        "sphinx": "",
        "xapian": "wiki",
        "moses": "",
        "shore": "",
    }

    CLIENT_DATA_MAPS = {
        "img-dnn": "img-dnn/mnist",
        "sphinx": "",
        "xapian": "terms.in",
        "moses": "",
        "shore": "",
    }

    # FIXME: hard-coded
    PORT_MAPS = {
        "img-dnn": 7311,
        "sphinx": 7312,
        "xapian": 7313,
        "moses": 7314,
        "shore": 7315,
    }

    # FIXME: hard-coded
    WARMUP_REQS = {
        "img-dnn": 1000,
        "sphinx": 10,
        "xapian": 1000,
        "moses": 1000,
        "shore": 1000,
    }

    # FIXME: hard-coded
    MAX_REQS = {
        "img-dnn": 10000,
        "sphinx": 100,
        "xapian": 10000,
        "moses": 1000,
        "shore": 1000,
    }

    # FIXME: hard-coded as MIN QPS
    QPS = {
        "img-dnn": 1000,
        "sphinx": 10,
        "xapian": 1000,
        "moses": 100,
        "shore": 100,
    }

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in NTailDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        wl_name = NTailDriver.workload_name
        for process in self._async_proc_info.children(recursive=True):

            if wl_name == 'sphinx':
                target_name = f'decoder_server_networked'
            else:
                target_name = f'{NTailDriver.workload_name}_server_networked'
            print(f'[_find_bench_proc] process.name(): {process.name()}, target_name: {target_name}')
            print(f'[_find_bench_proc] process.pid: {process.pid}, self.async_proc_info.pid: {self.async_proc_info.pid}')
            if process.name() == target_name:
                return process
        return None

    async def process_bench_output(self, bench_output_logger: logging.Logger) -> bool:
        ended = False
        finish_words = "end of tail bench"

        read_bytes = 1 << 20    # 1M Bytes, This is hard-coded, you can change it if you want to change it!
        recvd = await NTailDriver.reader.read(read_bytes)

        if finish_words in recvd:
            ended = True

        recvd = recvd.replace('latencies: ', '')
        recvd = recvd.replace("end of tail bench\n", '')
        recvd = recvd.rstrip(' \n')
        bench_output_logger.info(recvd)
        return ended

    async def _start_server(self) -> asyncio.subprocess.Process:
        wl_name = NTailDriver.workload_name  # ex) img-dnn

        # NOTE: Do check shell script if it is working in background
        server_exec_cmd \
            = f'{self._bench_home}/{wl_name}/run-server.sh'

        print(f'[_start_server] server_exec_cmd: {server_exec_cmd}')
        return await self._cgroup.exec_command(server_exec_cmd, stdout=asyncio.subprocess.PIPE)

    async def start_async_client(self) -> None:
        wl_name = NTailDriver.workload_name
        try:
            print(f'[start_async_client] Trying AsyncSSH connection...')

            conn = await asyncssh.connect('147.46.240.226', username='dcslab')

            print(f'[start_async_client] connected! {conn}')
            """
            client_env_args = {
                'TBENCH_CLIENT_THREADS': '1',
                'TBENCH_SERVER': '147.46.242.201',
                'TBENCH_SERVER_PORT': str(NTailDriver.PORT_MAPS[wl_name]),
                'TBENCH_QPS': str(NTailDriver.QPS[wl_name]),
                'TBENCH_MINSLEEPNS': '0',
                'TBENCH_RANDSEED': '0',
                'TBENCH_MNIST_DIR': str(NTailDriver.client_input_path)+'/'+str(NTailDriver.CLIENT_DATA_MAPS[wl_name])
            }
            """
            client_env_args = await self.get_client_env()
            print(f'[start_async_client] client_env_args: {client_env_args}')
            if wl_name == 'sphinx':
                client_bench_cmd = f'/ssd2/tailbench/tailbench/{wl_name}/decoder_client_networked'
            else:
                client_bench_cmd = f'/ssd2/tailbench/tailbench/{wl_name}/{wl_name}_client_networked'
            exec_cmd = client_bench_cmd + '\n'

            stdin, stdout, stderr = await conn.open_session(env=client_env_args)

            print(f'[start_async_client] open_session, stdin: {stdin}')
            print(f'[start_async_client] open_session, stdout: {stdout}')
            print(f'[start_async_client] open_session, stderr: {stderr}')

            stdin.write(exec_cmd)

            print(f'[start_async_client] send exec_command, and I\'m alive!! ')

            NTailDriver.reader = stdout
            print(f'[start_async_client] NTailDriver.reader: {NTailDriver.reader}')

        except asyncssh.ChannelOpenError as e:
            print(f'[start_async_client:except] AsyncSSH connection failed!')
            print(f'[start_async_client:except] error : {e}')
        finally:
            print(f'[start_async_client:finally] AsyncSSH conn: {conn}')
            print(f'[start_async_client:finally] exec_cmd: {exec_cmd}')
            print(f'[start_async_client:finally] NTailDriver.reader: {NTailDriver.reader}')

    async def get_client_env(self) -> Dict:
        wl_name = NTailDriver.workload_name
        if self._qps is not None:
            client_qps = str(self._qps)
        else:
            client_qps = str(NTailDriver.QPS[wl_name])

        base_env_args = {
            'TBENCH_CLIENT_THREADS': '1',
            'TBENCH_SERVER': '147.46.242.201',
            'TBENCH_SERVER_PORT': str(NTailDriver.PORT_MAPS[wl_name]),
            'TBENCH_QPS': client_qps,
            'TBENCH_MINSLEEPNS': '0',
            'TBENCH_RANDSEED': '0'
        }
        # FIXME: hard-coded
        if wl_name == 'img-dnn':
            extra_env_args = {
                'TBENCH_MNIST_DIR': NTailDriver.client_input_path+'/'+str(NTailDriver.CLIENT_DATA_MAPS[wl_name])
            }
        elif wl_name == 'sphinx':
            extra_env_args = {
                'TBENCH_AN4_CORPUS': NTailDriver.client_input_path+'/'+wl_name,
                'TBENCH_AUDIO_SAMPLES': NTailDriver.client_base_path+'/'+wl_name+'/'+'audio_samples'
            }
        elif wl_name == 'xapian':
            extra_env_args = {
                'TBENCH_TERMS_FILE': NTailDriver.client_input_path+'/'+wl_name+'/'+NTailDriver.CLIENT_DATA_MAPS[wl_name]
            }
        else:
            extra_env_args = {}

        client_env_args = dict(base_env_args, **extra_env_args)     # Merge `extra_env_args` to `base_env_args`

        return client_env_args

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        workload_name = self._name
        print(f'workload_name: {workload_name}')
        NTailDriver.workload_name = workload_name.lstrip('ntail').lstrip('-')
        print(f'NTailDriver.workload_name: {NTailDriver.workload_name}')

        NTailDriver.server_proc = await self._start_server()
        print(f'NTailDriver.server_proc.pid: {NTailDriver.server_proc.pid} ')
        time.sleep(2)
        # FIXME: If you want to invoke multiple clients, make the below code
        await self.start_async_client()
        print(f'NTailDriver.client_proc: {NTailDriver.reader}')

        return NTailDriver.server_proc
