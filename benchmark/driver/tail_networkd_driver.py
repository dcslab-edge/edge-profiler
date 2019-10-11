# coding: UTF-8

import asyncio
import asyncssh
from typing import Optional, Set

import psutil
import logging
from benchmark.driver.base_driver import BenchDriver
import time
import paramiko
import socket


class NTailDriver(BenchDriver):
    
    _benches: Set[str] = {'ntail-img-dnn', 'ntail-masstree', 'ntail-silo', 'ntail-sphinx',
                          'ntail-xapian', 'ntail-moses', 'ntail-shore', 'ntail-specjbb'}
    bench_name: str = 'tail'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)
    workload_name = None
    server_proc = None
    client_proc = None          # for client connected via ssh
    client_proc_stdout = None   # for client stdout
    client_proc_stderr = None   # for client stderr
    channel = None

    stdin = None    # used for sending commands
    stdout = None   # used for receiving results

    reader = None    # session used for receiving results by using AsyncSSH
    session = None   # session used for receiving results by using AsyncSSH

    # FIXME: hard-coded
    server_input_path = '/ssd/tailbench/tailbench.inputs'
    client_input_path = '/ssd2/tailbench/tailbench.inputs'
    # TODO: DATA_MAPS currently works on img-dnn only
    SERVER_DATA_MAPS = {
        "img-dnn": "models/model.xml",
        "sphinx": "models/model.xml",
        "xapian": "models/model.xml",
        "moses": "",
        "shore": "",
    }

    CLIENT_DATA_MAPS = {
        "img-dnn": "img-dnn/mnist",
        "sphinx": "models/model.xml",
        "xapian": "models/model.xml",
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
        "sphinx": 1000,
        "xapian": 1000,
        "moses": 1000,
        "shore": 1000,
    }

    # FIXME: hard-coded
    MAX_REQS = {
        "img-dnn": 9000,
        "sphinx": 9000,
        "xapian": 9000,
        "moses": 9000,
        "shore": 9000,
    }

    # FIXME: hard-coded
    QPS = {
        "img-dnn": 500,
        "sphinx": 100,
        "xapian": 100,
        "moses": 100,
        "shore": 100,
    }

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in NTailDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        for process in self._async_proc_info.children(recursive=True):
            target_name = f'{NTailDriver.workload_name}_server_networked'
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

    async def process_bench_output_temp(self, bench_output_logger: logging.Logger) -> bool:
        ignore_flag = False
        """
        bench_output_logger.info(f'self._bench_driver.is_running: {self._bench_driver.is_running}')
        bench_output_logger.info(f'self._bench_driver.async_proc.returncode: '
                                 f'{self._bench_driver.async_proc.returncode}')
        bench_output_logger.info(f'make_output: '
                                 f'{make_output}')
        """

        outdata = await self.waitStreams(NTailDriver.channel)
        outdata = outdata.replace("\r", '') # removing ^M in the text
        # bench_output_logger.info(f' outdata: {outdata}')   # output is very long line!
        if "queue times" or "latencies" in outdata:
            if "latencies:" in outdata or "times" in outdata:
                outdata = outdata.replace("latencies: ", '')
                bench_output_logger.info(outdata)
            if "end of tail bench" in outdata:
                outdata = outdata.replace("latencies: ", '')
                outdata = outdata.replace("end of tail bench\n", "")
                outdata = outdata.replace("(base) dcslab@bc5:~$", "")    # NOTE: DO NOT FIX!
                outdata = outdata.rstrip(' \n')
                bench_output_logger.info(outdata)
                NTailDriver.channel.close()
                return True
        return False

    async def waitStreams_temp(self, chan):
        #time.sleep(1)
        outdata = errdata = ""
        #print(f'[waitStreams] chan.recv_read(): {chan.recv_ready()}')
        while chan.recv_ready():
            recvd = chan.recv(4096).decode()
            #print(f'[waitStreams] recvd: {recvd}')
            outdata += recvd
            #outdata += chan.recv(4096).decode()
        #while chan.recv_stderr_ready():
        #    errdata += chan.recv_stderr(4096).decode()

        return outdata#, errdata

    async def _start_server(self) -> asyncio.subprocess.Process:
        wl_name = NTailDriver.workload_name  # ex) img-dnn

        # NOTE: Do check shell script if it is working in background
        server_exec_cmd \
            = f'{self._bench_home}/{wl_name}/run-server.sh'

        print(f'[_start_server] server_exec_cmd: {server_exec_cmd}')
        return await self._cgroup.exec_command(server_exec_cmd, stdout=asyncio.subprocess.PIPE)

    # async def _start_client(self):
    #     wl_name = NTailDriver.workload_name
    #     ssh = paramiko.SSHClient()
    #     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #     ssh.connect('147.46.240.226', username='dcslab')
    #
    #     # FIXME: hard-coded for img-dnn (e.g., TBENCH_MNIST_DIR)
    #     client_env_args = {
    #         'TBENCH_CLIENT_THREADS': '1',
    #         'TBENCH_SERVER': '147.46.242.201',
    #         'TBENCH_SERVER_PORT': str(NTailDriver.PORT_MAPS[wl_name]),
    #         'TBENCH_QPS': str(NTailDriver.QPS[wl_name]),
    #         'TBENCH_MINSLEEPNS': '0',
    #         'TBENCH_RANDSEED': '0',
    #         'TBENCH_MNIST_DIR': str(NTailDriver.client_input_path)+'/'+str(NTailDriver.CLIENT_DATA_MAPS[wl_name])
    #     }
    #     # NOTE: Do not make below cmd as background (DO NOT ATTACH "&" to end of client_bench_cmd)
    #     client_bench_cmd = f'/ssd2/tailbench/tailbench/{wl_name}/{wl_name}_client_networked'
    #     print(f'client_bench_cmd: {client_bench_cmd}')
    #     stdin, stdout, stderr = ssh.exec_command(client_bench_cmd, environment=client_env_args)
    #
    #     NTailDriver.client_proc = ssh
    #     NTailDriver.client_proc_stdout = stdout
    #     NTailDriver.client_proc_stderr = stderr
    #     return ssh

    @staticmethod
    async def _start_client():
        wl_name = NTailDriver.workload_name
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('147.46.240.226', username='dcslab')

        # FIXME: hard-coded for img-dnn (e.g., TBENCH_MNIST_DIR)
        client_env_args = {
            'TBENCH_CLIENT_THREADS': '1',
            'TBENCH_SERVER': '147.46.242.201',
            'TBENCH_SERVER_PORT': str(NTailDriver.PORT_MAPS[wl_name]),
            'TBENCH_QPS': str(NTailDriver.QPS[wl_name]),
            'TBENCH_MINSLEEPNS': '0',
            'TBENCH_RANDSEED': '0',
            'TBENCH_MNIST_DIR': str(NTailDriver.client_input_path)+'/'+str(NTailDriver.CLIENT_DATA_MAPS[wl_name])
        }
        # NOTE: Do not make below cmd as background (DO NOT ATTACH "&" to end of client_bench_cmd)
        client_bench_cmd = f'/ssd2/tailbench/tailbench/{wl_name}/{wl_name}_client_networked'
        print(f'client_bench_cmd: {client_bench_cmd}')
        #stdin, stdout, stderr = ssh.exec_command(client_bench_cmd, environment=client_env_args)

        #NTailDriver.client_proc = ssh
        #NTailDriver.client_proc_stdout = stdout
        #NTailDriver.client_proc_stderr = stderr
        channel = ssh.invoke_shell()
        #channel.setblocking(0)
        NTailDriver.channel = channel

        env_line = ""
        for k, v in client_env_args.items():
            line = f'{k}={v} '
            env_line += line

        exec_cmd = env_line + client_bench_cmd + '\n'
        #channel.send(exec_cmd)

        NTailDriver.stdin = channel.makefile('wb')
        NTailDriver.stdout = channel.makefile('r')
        NTailDriver.stdin.write(exec_cmd)
        NTailDriver.stdin.flush()

        return ssh

    @staticmethod
    async def start_async_client() -> None:
        wl_name = NTailDriver.workload_name
        try:
            print(f'[start_async_client] Trying AsyncSSH connection...')

            conn = await asyncssh.connect('147.46.240.226', username='dcslab')
            #reader, writer = await conn.open_session(command=client_bench_cmd, env=client_env_args)
            print(f'[start_async_client] connected! {conn}')

            client_env_args = {
                'TBENCH_CLIENT_THREADS': '1',
                'TBENCH_SERVER': '147.46.242.201',
                'TBENCH_SERVER_PORT': str(NTailDriver.PORT_MAPS[wl_name]),
                'TBENCH_QPS': str(NTailDriver.QPS[wl_name]),
                'TBENCH_MINSLEEPNS': '0',
                'TBENCH_RANDSEED': '0',
                'TBENCH_MNIST_DIR': str(NTailDriver.client_input_path)+'/'+str(NTailDriver.CLIENT_DATA_MAPS[wl_name])
            }
            client_bench_cmd = f'/ssd2/tailbench/tailbench/{wl_name}/{wl_name}_client_networked'
            exec_cmd = client_bench_cmd + '\n'
            #test_cmd = f'echo hello asyncssh\n'
            #channel, session = await conn.open_session(command=exec_cmd, env=client_env_args)
            stdin, stdout, stderr = await conn.open_session(env=client_env_args)
            #print(f'[start_async_client] open_session, ret: {ret}')
            print(f'[start_async_client] open_session, stdin: {stdin}')
            print(f'[start_async_client] open_session, stdout: {stdout}')
            print(f'[start_async_client] open_session, stderr: {stderr}')

            stdin.write(exec_cmd)
            #print(f'[start_async_client] open_session, chan: {channel}')
            #print(f'[start_async_client] open_session, session: {session}')

            print(f'[start_async_client] send exec_command, and I\'m alive!! ')

            NTailDriver.reader = stdout
            print(f'[start_async_client] NTailDriver.reader: {NTailDriver.reader}')

        except asyncssh.ChannelOpenError as e:
            print(f'[start_async_client:except] AsyncSSH connection failed!')
            print(f'[start_async_client:except] error : {e}')
        finally:
            print(f'[start_async_client:finally] AsyncSSH conn: {conn}')
            print(f'[start_async_client:finally] NTailDriver.reader: {NTailDriver.reader}')

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        workload_name = self._name
        print(f'workload_name: {workload_name}')
        NTailDriver.workload_name = workload_name.lstrip('ntail').lstrip('-')
        print(f'NTailDriver.workload_name: {NTailDriver.workload_name}')

        NTailDriver.server_proc = await self._start_server()
        print(f'NTailDriver.server_proc.pid: {NTailDriver.server_proc.pid}')
        time.sleep(2)
        # FIXME: If you want to invoke multiple clients, make the below code
        #NTailDriver.client_proc = await NTailDriver._start_client()
        await NTailDriver.start_async_client()
        print(f'NTailDriver.client_proc: {NTailDriver.reader}')
        #print(f'NTailDriver.client_proc.pid: {NTailDriver.client_proc.pid}')

        return NTailDriver.server_proc
        # return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL)
