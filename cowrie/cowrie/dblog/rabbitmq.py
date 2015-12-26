#
# this module uses the dblog feature to create a "traditional" looking logfile
# ..so not exactly a dblog.
#

from time import gmtime, strftime
from kippo.core import dblog
import pika
import uuid


class DBLogger(dblog.DBLogger):
    def start(self, cfg):
        self.host = cfg.get('database_rabbitmq', 'host')
        self.port = cfg.get('database_rabbitmq', 'port')
        self.exchange = cfg.get('database_rabbitmq', 'exchange')
        self.user = cfg.get('database_rabbitmq', 'user')
        self.password = cfg.get('database_rabbitmq', 'password')
        self.virtual_host = cfg.get('database_rabbitmq', 'virtual_host')
        self.meta = {}
        # self.channel.queue_declare(queue=self.queue, durable=True)

    def createSession(self, peerIP, peerPort, hostIP, hostPort):
        time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        session = uuid.uuid4().hex
        self.meta[session] = {'peerIP': peerIP, 'peerPort': peerPort, 'hostIP': hostIP, 'hostPort': hostPort, 'loggedin': None, 'credentials': [], 'version': None, 'ttylog': None, 'url': None, 'time': time}
        return session

    def handleConnectionLost(self, session, args):
        meta = self.meta[session]
        ttylog = self.ttylog(session)
        if ttylog:
            meta['ttylog'] = ttylog.encode('hex')
        credentials = pika.PlainCredentials(self.user, self.password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=str(self.host), port=int(self.port), credentials=credentials, virtual_host=self.virtual_host))
        channel = connection.channel()
        channel.basic_publish(exchange=self.exchange, routing_key='*', body=str(meta))
        channel.close()

    def handleLoginFailed(self, session, args):
        u, p = args['username'], args['password']
        self.meta[session]['credentials'].append((u, p))

    def handleLoginSucceeded(self, session, args):
        u, p = args['username'], args['password']
        self.meta[session]['loggedin'] = [u, p]

    def handleCommand(self, session, args):
        pass

    def handleUnknownCommand(self, session, args):
        pass

    def handleInput(self, session, args):
        pass

    def handleTerminalSize(self, session, args):
        pass

    def handleClientVersion(self, session, args):
        v = args['version']
        self.meta[session]['version'] = v

    def handleFileDownload(self, session, args):
        url = args['url']
        self.meta[session]['url'] = url

# vim: set sw=4 et:
