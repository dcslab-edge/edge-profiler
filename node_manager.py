#!/usr/bin/env python3
# coding: UTF-8

import json
import socket
import subprocess
from threading import Thread
from pathlib import Path
from benchmark.utils.machine_type import MachineChecker, NodeType


class NodeManager:
    # FIXME: hard coded
    #_NODE_IP = '147.46.242.201'     # Jetson1
    _NODE_IP = '147.46.242.243'    # Jetson2
    # _NODE_IP = '147.46.242.219'    # SDC1
    # _NODE_IP = '147.46.242.206'    # SDC2

    def __init__(self):
        self._ip_addr = NodeManager._NODE_IP
        self._port = '10020'
        self._node_mgr_path = Path.cwd() / 'node_mgr'
        self._node_type = MachineChecker.get_node_type()

    @property
    def ip_addr(self):
        return self._ip_addr

    @property
    def port(self):
        return self._port

    def job_listener(self, sock):
        while True:
            req = sock.recv(1024).decode()
            if not req:
                break
            print(f'{req}')
            output = self.parse_request(req)
            config_file = self.make_config_json(output)
            self.invoke_new_bench(req, config_file)

        sock.close()

    def parse_request(self, request: str):
        if not self._node_mgr_path.exists():
            self._node_mgr_path.mkdir(parents=True)
        req = request.split(',')
        bench_name = req[0]         # job_name          e.g., SparkDSLRCpu
        bench_type = req[1]         # job_type          e.g., bg
        bench_preferences = req[2]  # job_preferences   e.g., cpu
        return bench_name, bench_type, bench_preferences

    def make_config_json(self, job_description):
        bench_name = job_description[0]
        bench_type = job_description[1]
        bench_preference = job_description[2]
        config_file = self._node_mgr_path / f'{bench_name}_{bench_type}_{bench_preference}' / 'config.json'

        # FIXME: hard coded
        # Dict[str, Dict[str, Any]]
        output = dict()
        config = dict()
        config["name"] = bench_name
        config["type"] = bench_type
        config["num_of_threads"] = 2
        if self._node_type == NodeType.IntegratedGPU:
            config["binding_cores"] = "0,3-5"
        elif self._node_type == NodeType.CPU:
            config["binding_cores"] = "0-3"
        config["numa_nodes"] = "0"
        config["cpu_freq"] = 2.1
        config["cpu_percent"] = 100
        if self._node_type == NodeType.IntegratedGPU:
            config["gpu_freq"] = 1300500000

        output["workloads"] = config

        with config_file.open('w') as fp:
            fp.seek(0)
            json.dump(output, fp, indent=4)
        return config_file

    def run_server(self, ip_addr: str, port: str):
        # FIXME: ip_addr should be host ip itself
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((ip_addr, int(port)))
            while True:
                s.listen(1)
                conn, addr = s.accept()
                t = Thread(target=self.job_listener, args=(conn,))
                t.start()

    @staticmethod
    def invoke_new_bench(request: str, config_file: Path):
        # request is assumed like 'SparkDSLRCpu','fg','cpu'
        print(f'invoke benches from {config_file}')
        print(f'request : {request}')
        subprocess.run(args=('python3.7', 'benchmark_launcher.py', f'{config_file}'),
                       check=True, encoding='ASCII', stdout=subprocess.DEVNULL)


def main():
    nm = NodeManager()
    ip = nm.ip_addr
    port = nm.port
    nm.run_server(ip, port)


if __name__ == '__main__':
    main()
