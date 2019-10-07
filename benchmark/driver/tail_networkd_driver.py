# coding: UTF-8

import asyncio
from typing import Optional, Set

import psutil
import logging
from benchmark.driver.base_driver import BenchDriver


class NTailDriver(BenchDriver):
    
    _benches: Set[str] = {'tail-img-dnn', 'tail-masstree', 'tail-silo', 'tail-sphinx',
                          'tail-xapian', 'tail-moses', 'tail-shore', 'tail-specjbb'}
    bench_name: str = 'tail'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)
    workload_name = None
    server_proc = None
    client_proc = None

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in NTailDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        # bench_full_name = self._name
        # exec_name = bench_full_name.lstrip('tail').lstrip('-') + '_integrated'
        # print(f'[_find_bench_proc] bench_name: {bench_full_name}')
        # print(f'[_find_bench_proc] exec_name: {exec_name}')
        server_pid_file = f'{self._bench_home}/{self._workload_name}/server.pid'
        with open(server_pid_file, "r") as fp:
            server_pid = fp.read()

        print(f'[_find_bench_proc] server_pid: {server_pid}')
        if server_pid is not None:
            return psutil.Process(int(server_pid))
        else:
            return None

    async def process_bench_output(self, bench_output_logger: logging.Logger) -> bool:
        ignore_flag = False
        """
        bench_output_logger.info(f'self._bench_driver.is_running: {self._bench_driver.is_running}')
        bench_output_logger.info(f'self._bench_driver.async_proc.returncode: '
                                 f'{self._bench_driver.async_proc.returncode}')
        bench_output_logger.info(f'make_output: '
                                 f'{make_output}')
        """
        #raw_line = await self.async_proc.stdout.readline()
        # FIXME: Need to be tested!
        raw_line = await NTailDriver.client_proc.stdout.readline()
        line = raw_line.decode().strip()
        # bench_output_logger.info(f'{line}')
        #ex) im_detect: 26/100 0.172s
        #ex) timer: 0.333 sec.
        # FIXME: below code is for client-side process

        if "latencies:" in line:
            # Eval: latency per image
            #splitted = line.split(', ')
            #latency_seconds = splitted
            latency_seconds = line.lstrip("latencies: ")
            bench_output_logger.info(latency_seconds)
            ignore_flag = False
        else:
            # IF "im_detect:" not in `line` and "timer:" not in `line`
            ignore_flag = True
            if line == 'end of tail bench':
                return True

        #if not ignore_flag:
        #    bench_output_logger.info(latency_seconds)
        return False

    async def _start_server(self) -> asyncio.subprocess.Process:
        server_bench_path = f'{self._bench_home}/{self._workload_name}/run-server.sh'
        cmd = 'sh' + server_bench_path
        server_exec_cmd = f'{cmd}'
        return await self._cgroup.exec_command(server_exec_cmd, stdout=asyncio.subprocess.PIPE)

    async def _start_client(self) -> asyncio.subprocess.Process:
        # FIXME: hard-coded client's bench path & remote_exec_cmd
        # TODO: test for invoking run-client.sh by using `ssh` command
        # TODO: checking if client's output is delivered to `edge-profiler`
        client_bench_path = f'/ssd2/tailbench/tailbench/{self._workload_name}/run-client.sh'
        cmd = 'sh' + client_bench_path
        client_exec_cmd = f'ssh dcslab@147.46.240.226 \'{cmd}\''   # hard-coded for `bc5`
        return await self._cgroup.exec_command(client_exec_cmd, stdout=asyncio.subprocess.PIPE)

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        workload_name = self._name
        print(f'workload_name: {workload_name}')
        self._workload_name = workload_name.lstrip('tail').lstrip('-')
        print(f'workload_name: {self._workload_name}')

        NTailDriver.server_proc = self._start_server()
        # FIXME: If you want to invoke multiple clients, make the below code 
        NTailDriver.client_proc = self._start_client()

        return await NTailDriver.server_proc
        # return await self._cgroup.exec_command(cmd, stdout=asyncio.subprocess.DEVNULL)
