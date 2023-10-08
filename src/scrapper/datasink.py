import logging
from abc import abstractmethod


class DataSink:
    def __init__(self, name):
        self._name = name
        self._logger = logging.getLogger(f'sink-{name}')

    @abstractmethod
    def on_mushroom(self, lat, lon, url):
        pass
