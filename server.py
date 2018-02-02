#!/usr/bin/python
"""
Run: twistd -ny server.py
"""
import os
import sys
from os.path import join

from shapely.ops import transform
from shapely.geometry import Polygon, Point
from twisted.application import service
from twisted.application import strports  # pip install twisted
from twisted.internet import protocol
from twisted.python import log
from txws import WebSocketFactory  # pip install txws

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

from common import make_sure_path_exists, OUTPUT_DIR, project


class LocalDataSupplier:
    def __init__(self, on_found_latlon):
        self.on_found_latlon = on_found_latlon
        make_sure_path_exists(OUTPUT_DIR)
        self.latlonsfile = join(OUTPUT_DIR, "latlons.txt")

    def retrieve_local_data(self, roi):
        with open(self.latlonsfile, "r") as f:
            for l in f:
                try:
                    lat, lon, url = l.split(' ')
                    point = transform(project, Point(float(lon), float(lat)))
                    if not roi.contains(point):
                        continue
                    self.on_found_latlon(lat, lon, url)
                except Exception as e:
                    print(e)


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
        self.transport.write(data)  # send back

    def __process_input(self, msg):
        line = msg.strip()
        commands = line.split(' ')
        key = commands[0].lower().strip()
        if key == 'update':
            print('starting...')
            coords = []
            try:
                print("commands are ", commands[1])
                for c in commands[1].strip(';').split(';'):
                    (lat, lon) = c.split(',')
                    coords.append((float(lon), float(lat)))
            except Exception as e:
                print("Exception occured: ", str(e))
                return
            roi = transform(project, Polygon(coords))
            self.data_supplier.retrieve_local_data(roi)
        elif key == 'roi':
            print(line)
            # self.scrapper.set_roi()

    def __on_found_latlon(self, lat, lon, url):
        self._send("LATLONS {} {} {}".format(lat, lon, url))


application = service.Application("ws-cli")
ip = "localhost"
port = 8076
_echofactory = protocol.Factory()
_echofactory.protocol = Protocol
strports.service("tcp:{}:interface={}".format(port, ip),
                 WebSocketFactory(_echofactory)).setServiceParent(application)
