# coding: UTF-8


class RabbitMQConfig:
    def __init__(self, host_name: str, creation_exchange_name: str):
        self._host_name: str = host_name
        self._creation_exchange_name: str = creation_exchange_name

    @property
    def host_name(self):
        return self._host_name

    @property
    def creation_exchange_name(self):
        return self._creation_exchange_name
