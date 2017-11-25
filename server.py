#!/usr/bin/python
"""WebSocket CLI interface.
Install: pip install twisted txws
Run: twistd -ny wscli.py
Visit http://localhost:8084/
"""
from threading import Thread

import vk
from twisted.application import service
from twisted.application import strports  # pip install twisted
from twisted.internet import protocol
from twisted.internet.protocol import Factory
from twisted.python import log
from txws import WebSocketFactory  # pip install txws
import os
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
from scrapper import VkScrapper


class Protocol(protocol.Protocol):

    def connectionMade(self):
        log.msg("launch a new process on each new connection")
        with open('tokens.txt') as f:
            tokens = [l.strip() for l in f]

        if len(tokens) == 0:
            print("No tokens found!")
            exit(0)

        session = vk.Session(access_token=tokens[0])
        vkapi = vk.API(session)

        self.scrapper = VkScrapper(vkapi, self.__on_found_latlon)
        self.scrapper_thread = Thread(target=self.scrapper.get_locations_by_groups)
        self.scrapper_thread.start()
        self.started = True
        self.loaded_local_data = False

    def dataReceived(self, data):
        try:
            msg = data.decode('utf-8')
            log.msg("Received data: " + msg)
            self.__process_input(msg)
        except Exception as e:
            print(str(e))
            print("exception parsing %r" % data)

    def connectionLost(self, reason):
        self.transport.loseConnection()
        self.scrapper.stop()
        self.scrapper_thread.join()
        self.scrapper.close()

    def _send(self, data):
        self.transport.write(data) # send back

    def __process_input(self, msg):
        line = msg.strip()
        commands = line.split(' ')
        key = commands[0].lower().strip()
        if key == 'start':
            print('starting...')
            coords = []
            try:
                for c in commands[1].split(';'):
                    (lat, lon) = c.split(',')
                    coords.append((float(lon), float(lat)))
            except Exception as e:
                pass
            self.scrapper.set_roi(coords)

            if not self.loaded_local_data:
                self.scrapper.retrieve_local_data()

            self.scrapper.start()
        elif key == 'roi':
            print(line)
            #self.scrapper.set_roi()
        elif key == 'pause':
            print('pausing...')
            self.scrapper.pause()
        elif key == 'stop':
            print('stopping...')
            self.scrapper.stop()


    def __on_found_latlon(self, lat, lon, url):
        self._send("LATLONS {} {} {}".format(lat, lon, url))


application = service.Application("ws-cli")

_echofactory = protocol.Factory()
_echofactory.protocol = Protocol
strports.service("tcp:8076:interface=127.0.0.1",
                 WebSocketFactory(_echofactory)).setServiceParent(application)
