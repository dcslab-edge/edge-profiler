#!/usr/bin/env python3
# coding: UTF-8

import asyncio
import functools
import json
import logging
import os
import time
from concurrent.futures import CancelledError
from itertools import chain
from logging import Formatter, Handler, LogRecord
from pathlib import Path
from signal import SIGCONT, SIGSTOP
from typing import Any, Callable, Generator, Optional

import pika
import psutil
from coloredlogs import ColoredFormatter
from pika.adapters.blocking_connection import BlockingChannel

from benchmark.driver.base_driver import BenchDriver
from containers import BenchConfig, PerfConfig, RabbitMQConfig, TegraConfig
from .utils.machine_type import MachineChecker, NodeType


class Benchmark:
    class _Decorators:
        @staticmethod
        def ensure_running(func: Callable[['Benchmark', Any], Any]):
            @functools.wraps(func)
            def decorator(self: 'Benchmark', *args, **kwargs):
                if not self.is_running:
                    raise RuntimeError(f'The benchmark ({self._identifier}) has already ended or never been invoked.'
                                       ' Run benchmark first via invoking `run()`!')
                return func(self, *args, **kwargs)

            return decorator

        @staticmethod
        def ensure_not_running(func: Callable[['Benchmark', Any], Any]):
            @functools.wraps(func)
            def decorator(self: 'Benchmark', *args, **kwargs):
                if self.is_running:
                    raise RuntimeError(f'benchmark {self._bench_driver.pid} is already in running.')
                return func(self, *args, **kwargs)

            return decorator

        @staticmethod
        def ensure_invoked(func: Callable[['Benchmark', Any], Any]):
            @functools.wraps(func)
            def decorator(self: 'Benchmark', *args, **kwargs):
                if not self._bench_driver.has_invoked:
                    raise RuntimeError(f'benchmark {self._identifier} is never invoked.')
                return func(self, *args, **kwargs)

            return decorator

    _file_formatter = ColoredFormatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] (%(funcName)s:%(lineno)d in %(filename)s) $ %(message)s')
    _stream_formatter = ColoredFormatter('%(asctime)s.%(msecs)03d [%(levelname)8s] %(name)14s $ %(message)s')

    def __init__(self, identifier: str, bench_config: BenchConfig, perf_config: PerfConfig, tegra_config: TegraConfig,
                 rabbit_mq_config: RabbitMQConfig, workspace: Path, max_benches: int, logger_level: int = logging.INFO):
        self._identifier: str = identifier
        self._perf_config: PerfConfig = perf_config
        self._tegra_config: TegraConfig = tegra_config
        self._rabbit_mq_config: RabbitMQConfig = rabbit_mq_config

        self._bench_driver: BenchDriver = bench_config.generate_driver(identifier)
        self._perf: Optional[asyncio.subprocess.Process] = None
        self._tegra: Optional[asyncio.subprocess.Process] = None
        self._max_benches: int = max_benches
        self._end_time: Optional[float] = None
        self._node_type = MachineChecker.get_node_type()

        perf_parent = workspace / 'perf'
        if not perf_parent.exists():
            perf_parent.mkdir()

        # perf_csv contains both info of `perf` and `tegrastats`
        self._perf_csv: Path = perf_parent / f'{identifier}.csv'

        log_parent = workspace / 'logs'
        if not log_parent.exists():
            log_parent.mkdir()

        self._log_path: Path = log_parent / f'{identifier}.log'

        # setup for loggers

        logger = logging.getLogger(self._identifier)
        logger.setLevel(logger_level)

        metric_logger = logging.getLogger(f'{self._identifier}-rabbitmq')
        metric_logger.setLevel(logger_level)

    @_Decorators.ensure_not_running
    async def start_and_pause(self, print_log: bool = False):
        self._remove_logger_handlers()

        # setup for loggers

        logger = logging.getLogger(self._identifier)

        fh = logging.FileHandler(self._log_path, mode='w')
        fh.setFormatter(Benchmark._file_formatter)
        logger.addHandler(fh)

        if print_log:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(Benchmark._stream_formatter)
            logger.addHandler(stream_handler)

        # launching benchmark

        logger.info('Starting benchmark...')
        await self._bench_driver.run()
        logger.info(f'The {self._bench_driver.wl_type} benchmark has started. pid : {self._bench_driver.pid}')

        self._pause_bench()

    @_Decorators.ensure_running
    async def monitor(self, print_metric_log: bool = False):
        logger = logging.getLogger(self._identifier)
                
        try:
            # launching perf
            self._perf = await asyncio.create_subprocess_exec(
                    'perf', 'stat', '-e', self._perf_config.event_str,
                    '-p', str(self._bench_driver.pid), '-x', ',', '-I', str(self._perf_config.interval),
                    stderr=asyncio.subprocess.PIPE)

            # launching tegrastats
            # tegrastats uses stdout for printing
            if self._node_type == NodeType.IntegratedGPU:
                self._tegra = await asyncio.create_subprocess_exec(
                    'sudo', '/home/nvidia/tegrastats', '--interval', str(self._tegra_config.interval),
                    stdout=asyncio.subprocess.PIPE)

            # setup for metric logger
            # rabiit_mq is used to read perf values
            # tegra-config files are added just in case but not used
            if self._node_type == NodeType.IntegratedGPU:
                rabbit_mq_handler = RabbitMQHandler(self._rabbit_mq_config, self._bench_driver.name,
                                                    self._bench_driver.wl_type, self._bench_driver.pid,
                                                    self._perf.pid, self._perf_config.interval,
                                                    self._tegra.pid, self._tegra_config.interval,
                                                    self._max_benches)
                rabbit_mq_handler.setFormatter(RabbitMQFormatter(self._perf_config.event_names,
                                                                 self._tegra_config.event_names))

            elif self._node_type == NodeType.CPU:
                rabbit_mq_handler = RabbitMQHandler(self._rabbit_mq_config, self._bench_driver.name,
                                                    self._bench_driver.wl_type, self._bench_driver.pid,
                                                    self._perf.pid, self._perf_config.interval, None, None,
                                                    self._max_benches)
                rabbit_mq_handler.setFormatter(RabbitMQFormatter(self._perf_config.event_names, None))

            metric_logger = logging.getLogger(f'{self._identifier}-rabbitmq')
            metric_logger.addHandler(rabbit_mq_handler)

            if print_metric_log:
                metric_logger.addHandler(logging.StreamHandler())

            with self._perf_csv.open('w') as fp:
                # print csv header
                fp.write(','.join(self._perf_config.event_names))
                if self._node_type == NodeType.IntegratedGPU:
                    fp.write(',gpu_core_util,gpu_core_freq,gpu_emc_util,gpu_emc_freq'+'\n')

            metric_logger.addHandler(logging.FileHandler(self._perf_csv))

            # perf polling loop

            num_of_events = len(self._perf_config.events)
            while self._bench_driver.is_running and self._perf.returncode is None:
                record = []
                ignore_flag = False

                for _ in range(num_of_events):
                    raw_line = await self._perf.stderr.readline()
                    line = raw_line.decode().strip()
                    try:
                        value = line.split(',')[1]
                        float(value)
                        record.append(value)
                    except (IndexError, ValueError) as e:
                        ignore_flag = True
                        logger.debug(f'a line that perf printed was ignored due to following exception : {e}'
                                     f' and the line is : {line}')
                if self._node_type == NodeType.IntegratedGPU:
                    # tegra data append(gr3d, gr3dfreq, emc, emcfreq)
                    raw_tegra_line = await self._tegra.stdout.readline()
                    for rec in self.tegra_parser(raw_tegra_line):
                        record.append(rec)

                if not ignore_flag:
                    metric_logger.info(','.join(record))

            logger.info('end of monitoring loop')

            self._kill_perf()
            if self._node_type == NodeType.IntegratedGPU:
                self._kill_tegra()

        except CancelledError as e:
            logger.debug(f'The task cancelled : {e}')
            self._stop()

        finally:
            try:
                self._kill_perf()
                if self._node_type == NodeType.IntegratedGPU:
                    self._kill_tegra()
                self._bench_driver.stop()
            except (psutil.NoSuchProcess, ProcessLookupError):
                pass

            await self._bench_driver.cleanup()
            logger.info('The benchmark is ended.')
            self._remove_logger_handlers()
            self._end_time = time.time()

    @staticmethod
    def tegra_parser(tegrastatline):
        """
        parses tegrastats line information for GR3D & EMC with freq
        :param tegrastatline:
        :return:
        """
        _tegra_lists = tegrastatline.decode().strip().split(' ')

        def freq_parser(_utilfreq):
            val=_utilfreq.split('@')[0]
            return [val[:-1], _utilfreq.split('@')[1]]
        # [%,freq]
        emc_freq = freq_parser(_tegra_lists[7])
        gr3d_freq = freq_parser(_tegra_lists[9])

        return [gr3d_freq[0], gr3d_freq[1], emc_freq[0], emc_freq[1]]

    def _pause_bench(self):
        logging.getLogger(self._identifier).info('pausing...')

        self._bench_driver.pause()

    def pause(self):
        self._pause_bench()
        self._perf.send_signal(SIGSTOP)
        # Tegrastats
        if self._node_type == NodeType.IntegratedGPU:
            self._tegra.send_signal(SIGSTOP)

    @_Decorators.ensure_running
    def resume(self):
        logging.getLogger(self._identifier).info('resuming...')

        self._bench_driver.resume()
        if self._perf is not None and self._perf.returncode is None:
            self._perf.send_signal(SIGCONT)
        # Tegrastats
        if self._node_type == NodeType.IntegratedGPU:
            if self._tegra is not None and self._tegra.returncode is None:
                self._tegra.send_signal(SIGCONT)

    def _kill_perf(self):
        if self._perf is not None and self._perf.returncode is None:
            self._perf.kill()
        self._perf = None

    # Tegrastats
    def _kill_tegra(self):
        if self._tegra is not None and self._tegra.returncode is None:
            # tegra runs on sudo command...
            os.system("sudo kill %d"%(self._tegra.pid))

#            self._tegra.kill()
        self._tegra = None

    def _stop(self):
        logger = logging.getLogger(self._identifier)
        logger.info('stopping...')

        try:
            self._kill_perf()
            self._kill_tegra()
            self._bench_driver.stop()
        except (psutil.NoSuchProcess, ProcessLookupError) as e:
            logger.debug(f'Process already killed : {e}')

    def _remove_logger_handlers(self):
        logger = logging.getLogger(self._identifier)
        metric_logger = logging.getLogger(f'{self._identifier}-rabbitmq')

        for handler in tuple(metric_logger.handlers):  # type: Handler
            logger.debug(f'removing metric handler {handler}')
            metric_logger.removeHandler(handler)
            try:
                handler.flush()
                handler.close()
            except:
                logger.exception('Exception has happened while removing handler form metric logger.')

        for handler in tuple(logger.handlers):  # type: Handler
            logger.removeHandler(handler)
            handler.flush()
            handler.close()

    @property
    @_Decorators.ensure_invoked
    def launched_time(self) -> float:
        """
        The launched_time is different based on the benchmark name
        :return:
        """
        if(self._bench_driver.bench_name == 'data-stream'):
          return self._bench_driver.sparkGPU_launched_time
        else :
          return self._bench_driver.created_time

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def end_time(self) -> Optional[float]:
        return self._end_time

    @property
    def runtime(self) -> Optional[float]:
        if self._end_time is None:
            return None
        elif self._end_time < self.launched_time:
            return None
        else:
            return self._end_time - self.launched_time

    @property
    def is_running(self) -> bool:
        return self._bench_driver.is_running and (self._perf is None or self._perf.returncode is None)


class RabbitMQHandler(Handler):
    def __init__(self, rabbit_mq_config: RabbitMQConfig, bench_name: str, bench_type: str, bench_pid: int,
                 perf_pid: int, perf_interval: int, tegra_pid: Optional[int], tegra_interval: Optional[int],
                 max_benches: int):
        super().__init__()
        # TODO: upgrade to async version
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_mq_config.host_name))
        self._channel: BlockingChannel = self._connection.channel()

        self._queue_name: str = f'{bench_name}({bench_pid})'
        self._channel.queue_declare(queue=self._queue_name)

        # Notify creation of this benchmark to scheduler
        self._channel.queue_declare(queue=rabbit_mq_config.creation_q_name)
        self._channel.basic_publish(exchange='', routing_key=rabbit_mq_config.creation_q_name,
                body=f'{bench_name},{bench_type},{bench_pid},{perf_pid},{perf_interval},{tegra_pid},{tegra_interval},{max_benches}')

    def emit(self, record: LogRecord):
        formatted: str = self.format(record)

        self._channel.basic_publish(exchange='', routing_key=self._queue_name, body=formatted)

    def close(self):
        super().close()
        try:
            self._channel.queue_delete(self._queue_name)
        except:
            pass
        self._connection.close()

    def __repr__(self):
        level = logging.getLevelName(self.level)
        return f'<{self.__class__.__name__} {self._queue_name} ({level})>'


class RabbitMQFormatter(Formatter):
    def __init__(self, perf_events: Generator[str, Any, None], tegra_events: Optional[Generator[str, Any, None]]):
        super().__init__()
        self._event_names = tuple(perf_events)
        if tegra_events is not None:
            self._event_names += tuple(tegra_events)
        # print(self._event_names)
        self._req_num = 0

    @staticmethod
    def _convert_num(val: str):
        try:
            return int(val)
        except ValueError:
            pass

        try:
            return float(val)
        except ValueError:
            raise ValueError(f'{val} is neither an int nor a float.')

    def format(self, record: LogRecord) -> str:
        # print(record.msg)
        values = chain(map(self._convert_num, record.msg.split(',')), (self._req_num,))
        self._req_num += 1
        return json.dumps({k: v for k, v in zip(self._event_names, values)})
