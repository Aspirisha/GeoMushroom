#!/usr/bin/python
"""
Run: twistd -ny server.py
"""
import os
import sys
from threading import Thread

import vk
from twisted.application import service
from twisted.application import strports  # pip install twisted
from twisted.internet import protocol
from twisted.python import log
from txws import WebSocketFactory  # pip install txws

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
from scrapper import LocalDataSupplier


class Protocol(protocol.Protocol):

    def connectionMade(self):
        log.msg("launch a new process on each new connection")

        self.data_supplier = LocalDataSupplier(self.__on_found_latlon)

    def dataReceived(self, data):
        try:
            msg = data.decode('utf-8')
            print("Got message ", msg)
            log.msg("Received data: " + msg)
            self.__process_input(msg)
        except Exception as e:
            print(str(e))
            print("exception parsing %r" % data)

    def connectionLost(self, reason):
        print("Lost connection")
        self.transport.loseConnection()

    def _send(self, data):
        self.transport.write(data) # send back

    def __process_input(self, msg):
        line = msg.strip()
        commands = line.split(' ')
        key = commands[0].lower().strip()
        if key == 'update':
            print('starting...')
            coords = []
            try:
                for c in commands[1].split(';'):
                    (lat, lon) = c.split(',')
                    coords.append((float(lon), float(lat)))
            except Exception as e:
                pass
            self.data_supplier.set_roi(coords)

            self.data_supplier.retrieve_local_data()

            #self.scrapper.start()
        elif key == 'roi':
            print(line)
            #self.scrapper.set_roi()

    def __on_found_latlon(self, lat, lon, url):
        self._send("LATLONS {} {} {}".format(lat, lon, url))


application = service.Application("ws-cli")

_echofactory = protocol.Factory()
_echofactory.protocol = Protocol
strports.service("tcp:8076:interface=127.0.0.1",
                 WebSocketFactory(_echofactory)).setServiceParent(application)
