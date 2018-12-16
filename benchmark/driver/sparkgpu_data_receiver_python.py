# coding: UTF-8

import asyncio
import os
import shlex
from typing import Optional, Set
import time
import psutil

from benchmark.driver.base_driver import BenchDriver
from subprocess import Popen


class SparkGPUDataReceiverPythonDriver(BenchDriver):
    _benches: Set[str] = {"dataStreamProcess"}
    bench_name: str = 'spark-submit'
    _bench_home: str = BenchDriver.get_bench_home(bench_name)

    @staticmethod
    def has(bench_name: str) -> bool:
        return bench_name in SparkGPUDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        children = self._async_proc_info.children(True)

        if len(children) is 0:
            return None
        else:
            return children[0]

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        signal_invoker_home = BenchDriver.get_bench_home('signal-invoke')
        data_stream_python_home = BenchDriver.get_bench_home('data-stream-python')
        cmd = '{0}/bin/spark-submit {1}/receiver/sparkgpu_receiver_code.py'.format(self._bench_home, data_stream_python_home)

        env = os.environ.copy()
        env['M2_HOME'] = '/home/nvidia/.m2'
        env['MAVEN_HOME'] = '/home/nvidia/dcslab/packages/apache-maven-3.6.0'
        env['PATH'] = env['MAVEN_HOME'] + '/bin/:' + env['PATH']

        proc=Popen(['python3.7',signal_invoker_home+'/signal_invoker.py'])
        
        self.sparkGPU_launched_time = time.time()
        await self._cgroup.exec_command(cmd, env=env,
                                               stdout=asyncio.subprocess.DEVNULL,
                                               stderr=asyncio.subprocess.DEVNULL)
