# coding: UTF-8

import asyncio
import os
import shlex
from typing import Optional, Set

import psutil

from benchmark.driver.base_driver import BenchDriver


class SparkGPUDataReceiverScalaDriver(BenchDriver):
    _benches: Set[str] = {}
    bench_name: str = 'sparkgpu'
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
        data_stream_path = BenchDriver.get_bench_home('data-stream-scala')
        cmd = '{0}/bin/spark-submit --class com.dcslab.DataReceiver.SparkGPUDataReceiveScala {1}/receiver/target/sparkgpudatareceivescala-0.0.1-SNAPSHOT.jar localhost 8888'.format(self._bench_home, data_stream_path)

        env = os.environ.copy()
        env['M2_HOME'] = '/home/nvidia/.m2'
        env['MAVEN_HOME'] = '/home/nvidia/dcslab/packages/apache-maven-3.6.0'
        env['PATH'] = env['MAVEN_HOME'] + '/bin/:' + env['PATH']


        return await self._cgroup.exec_command(cmd, env=env,
                                               stdout=asyncio.subprocess.DEVNULL,
                                               stderr=asyncio.subprocess.DEVNULL)
