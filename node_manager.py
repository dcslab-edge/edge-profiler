#!/usr/bin/env python3
# coding: UTF-8


import socket
from threading import Thread


class NodeManager:
    # FIXME: hard coded
    _NODE_IP = '147.46.242.201'     # Jetson1
    # _NODE_IP = '147.46.242.243'    # Jetson2
    # _NODE_IP = '147.46.242.219'    # SDC1
    # _NODE_IP = '147.46.242.206'    # SDC2

    def __init__(self):
        self._ip_addr = NodeManager._NODE_IP
        self._port = '10020'

    @property
    def ip_addr(self):
        return self._ip_addr

    @property
    def port(self):
        return self._port

    @staticmethod
    def echo(sock):
        while True:
            data = sock.recv(1024)
            if not data:
                break
            #sock.send(f'{self._ip_addr}:{self._}')
            sock.sendall(data)
        sock.close()

    def run_server(self, ip_addr:str, port: str):
        #host = ''
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((ip_addr, int(port)))
            while True:
                s.listen(1)
                conn, addr = s.accept()
                t = Thread(target=self.echo, args=(conn,))
                t.start()


def main():
    nm = NodeManager()
    ip = nm.ip_addr
    port = nm.port
    nm.run_server(ip, port)


if __name__ == '__main__':
    main()
