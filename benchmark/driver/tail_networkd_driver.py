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

    workload_names = dict()
    server_procs = dict()
    readers = dict()    # session used for receiving results by using AsyncSSH

    # FIXME: hard-coded
    #server_base_path = '/ssd/tailbench/tailbench-v0.9'                 # jetson tx2 (for edge)
    #client_base_path = '/ssd2/tailbench/tailbench'                     # bc5 (for edge)
    #server_input_path = '/ssd/tailbench/tailbench.inputs'              # jetson tx2 (for edge)
    #client_input_path = '/ssd2/tailbench/tailbench.inputs'             # bc5 (for edge)
    server_base_path = '/ssd2/tailbench/tailbench'                              # bc5 (for xeon-HIS)
    client_base_path = '/home/dcslab/ysnam/benchmarks/tailbench/tailbench'      # bc4 (for xeon-HIS)
    server_input_path = '/ssd2/tailbench/tailbench.inputs'                              # bc5 (for xeon-HIS)
    client_input_path = '/home/dcslab/ysnam/benchmarks/tailbench/tailbench.inputs'      # bc4 (for xeon-HIS)

    # TODO: DATA_MAPS currently works on img-dnn only (?)
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
        "masstree": 7315,
        "silo": 7316,
    }

    # FIXME: hard-coded
    WARMUP_REQS = {
        "img-dnn": 1000,
        "sphinx": 10,
        "xapian": 1000,
        "moses": 1000,
        "masstree": 1000,
        "silo": 1000,
    }

    # FIXME: hard-coded
    MAX_REQS = {
        "img-dnn": 10000,
        "sphinx": 100,
        "xapian": 10000,
        "moses": 1000,
        "masstree": 1000,
        "silo": 1000,
    }

    # FIXME: hard-coded as MIN QPS
    QPS = {
        "img-dnn": 1000,
        "sphinx": 10,
        "xapian": 1000,
        "moses": 100,
        "masstree": 100,
        "silo": 100,
    }

    # def __init__(self, workload_name=None, server_proc=None, reader=None):
    #     super().__init__()
    #     self._workload_name = workload_name
    #     self._server_proc = server_proc
    #     self._reader = reader    # session used for receiving results by using AsyncSSH


    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in NTailDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        wl_name = NTailDriver.workload_names[self._name]
        for process in self._async_proc_info.children(recursive=True):

            if wl_name == 'sphinx':
                target_name = f'decoder_server_networked'
            elif wl_name == 'masstree':
                target_name = f'mttest_server_networked'
            else:
                target_name = f'{wl_name}_server_networked'
            #print(f'[_find_bench_proc] process.name(): {process.name()}, target_name: {target_name}')
            #print(f'[_find_bench_proc] process.pid: {process.pid}, self.async_proc_info.pid: {self.async_proc_info.pid}')
            if process.name() == target_name:
                return process
        return None

    async def process_bench_output(self, bench_output_logger: logging.Logger) -> bool:
        wl_name = NTailDriver.workload_names[self._name]
        ended = False
        finish_words = "end of tail bench"

        read_bytes = 1 << 20    # 1M Bytes, This is hard-coded, you can change it if you want to change it!
        recvd = await NTailDriver.readers[wl_name].read(read_bytes)

        if finish_words in recvd:
            ended = True

        recvd = recvd.replace('latencies: ', '')
        recvd = recvd.replace("end of tail bench\n", '')
        recvd = recvd.rstrip(' \n')
        bench_output_logger.info(recvd)
        return ended

    async def _start_server(self) -> asyncio.subprocess.Process:
        wl_name = NTailDriver.workload_names[self._name]  # ex) img-dnn

        # NOTE: Do check shell script if it is working in background
        #if wl_name == 'masstree':
        #    server_exec_cmd \
        #        = f'{self._bench_home}/{wl_name}/run-server.sh'
        #        #= f'sudo {self._bench_home}/{wl_name}/run-server.sh'
        #else:
        #    server_exec_cmd \
        #        = f'{self._bench_home}/{wl_name}/run-server.sh'
        server_exec_cmd \
            = f'{self._bench_home}/{wl_name}/run-server.sh'

        print(f'[_start_server] server_exec_cmd: {server_exec_cmd}')
        return await self._cgroup.exec_command(server_exec_cmd, stdout=asyncio.subprocess.PIPE)

    async def start_async_client(self) -> None:
        wl_name = NTailDriver.workload_names[self._name]
        try:
            print(f'[start_async_client] Trying AsyncSSH connection...')

            #conn = await asyncssh.connect('147.46.240.242', username='dcslab')  # bc3
            conn = await asyncssh.connect('147.46.240.229', username='dcslab')  # bc4

            print(f'[start_async_client] connected! {conn}')
            """
            client_env_args = {
                'TBENCH_CLIENT_THREADS': '1',
                'TBENCH_SERVER': '147.46.240.226',
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
                client_bench_cmd = f'/home/dcslab/ysnam/benchmarks/tailbench/tailbench/{wl_name}/decoder_client_networked'
            elif wl_name == 'moses':
                    client_bench_cmd = f'/home/dcslab/ysnam/benchmarks/tailbench/tailbench/{wl_name}/bin/moses_client_networked'
            elif wl_name == 'masstree':
                # chrt -r 99 : set real-time scheduling attributes of an existing pid with SCEHD_RR policy
                #client_bench_cmd = f'sudo chrt -r 99 /home/dcslab/ysnam/benchmarks/tailbench/tailbench/{wl_name}/mttest_client_networked'
                client_bench_cmd = f'/home/dcslab/ysnam/benchmarks/tailbench/tailbench/{wl_name}/mttest_client_networked'
            else:
                client_bench_cmd = f'/home/dcslab/ysnam/benchmarks/tailbench/tailbench/{wl_name}/{wl_name}_client_networked'
            exec_cmd = client_bench_cmd + '\n'

            stdin, stdout, stderr = await conn.open_session(env=client_env_args)
            """
            print(f'[start_async_client] open_session, stdin: {stdin}')
            print(f'[start_async_client] open_session, stdout: {stdout}')
            print(f'[start_async_client] open_session, stderr: {stderr}')
            """
            stdin.write(exec_cmd)

            #print(f'[start_async_client] send exec_command, and I\'m alive!! ')

            NTailDriver.readers[wl_name] = stdout
            #print(f'[start_async_client] NTailDriver.reader: {NTailDriver.readers[wl_name]}')

        except asyncssh.ChannelOpenError as e:
            print(f'[start_async_client:except] AsyncSSH connection failed!')
            print(f'[start_async_client:except] error : {e}')
        finally:
            print(f'[start_async_client:finally] AsyncSSH conn: {conn}')
            print(f'[start_async_client:finally] exec_cmd: {exec_cmd}')
            print(f'[start_async_client:finally] NTailDriver.reader: {NTailDriver.readers[wl_name]}')

    async def get_client_env(self) -> Dict:
        wl_name = NTailDriver.workload_names[self._name]
        if self._qps is not None:
            client_qps = str(self._qps)
        else:
            client_qps = str(NTailDriver.QPS[wl_name])

        base_env_args = {
            'TBENCH_CLIENT_THREADS': '1',
            'TBENCH_SERVER': '147.46.240.226',
            'TBENCH_SERVER_PORT': str(NTailDriver.PORT_MAPS[wl_name]),
            'TBENCH_QPS': client_qps,
            'TBENCH_MINSLEEPNS': '0',
            'TBENCH_RANDSEED': '0'
        }
        # FIXME: hard-coded
        #print(f'[get_client_env] wl_name: {wl_name}')
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

        #print(f'[get_client_env] extra_env_args: {extra_env_args}, type: {type(extra_env_args)}')
        #print(f'[get_client_env] client_env_args: {client_env_args}, type: {type(client_env_args)}')
        return client_env_args

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        workload_name = self._name  # ex) ntail-img-dnn
        print(f'workload_name: {workload_name}')
        NTailDriver.workload_names[workload_name] = workload_name.lstrip('ntail').lstrip('-') # ex) img-dnn
        print(f'NTailDriver.workload_name: {NTailDriver.workload_names[workload_name]}')

        wl_name = NTailDriver.workload_names[workload_name]
        NTailDriver.server_procs[wl_name] = await self._start_server()
        print(f'NTailDriver.server_proc.pid: {NTailDriver.server_procs[wl_name].pid} ')
        time.sleep(2)
        # FIXME: If you want to invoke multiple clients, make the below code
        await self.start_async_client()
        print(f'NTailDriver.readers: {NTailDriver.readers[wl_name]}')

        return NTailDriver.server_procs[wl_name]
