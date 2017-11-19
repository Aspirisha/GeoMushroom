#!/usr/bin/python
"""WebSocket CLI interface.
Install: pip install twisted txws
Run: twistd -ny wscli.py
Visit http://localhost:8084/
"""
import sys
from twisted.application import strports # pip install twisted
from twisted.application import service
from twisted.internet    import protocol
from twisted.python      import log
from twisted.web.server  import Site
from twisted.web.static  import File

from txws import WebSocketFactory # pip install txws


class Protocol(protocol.Protocol):
    def connectionMade(self):
        from twisted.internet import reactor
        log.msg("launch a new process on each new connection")
        self.pp = ProcessProtocol()
        self.pp.factory = self
        reactor.spawnProcess(self.pp, sys.executable,
                             [sys.executable, '-u', 'client.py'])
    def dataReceived(self, data):
        log.msg("redirect received data to process' stdin: %r" % data)
        self.pp.transport.write(data)
    def connectionLost(self, reason):
        self.pp.transport.loseConnection()

    def _send(self, data):
        self.transport.write(data) # send back


class ProcessProtocol(protocol.ProcessProtocol):
    def connectionMade(self):
        log.msg("connectionMade")
    def outReceived(self, data):
        log.msg("send stdout back %r" % data)
        self._sendback(data)
    def errReceived(self, data):
        log.msg("send stderr back %r" % data)
        self._sendback(data)
    def processExited(self, reason):
        log.msg("processExited")
    def processEnded(self, reason):
        log.msg("processEnded")

    def _sendback(self, data):
        self.factory._send(data)


application = service.Application("ws-cli")

_echofactory = protocol.Factory()
_echofactory.protocol = Protocol
strports.service("tcp:8076:interface=127.0.0.1",
                 WebSocketFactory(_echofactory)).setServiceParent(application)

resource = File('.') # serve current directory INCLUDING *.py files
strports.service("tcp:8084:interface=127.0.0.1",
                 Site(resource)).setServiceParent(application)