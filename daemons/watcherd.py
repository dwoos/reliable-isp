import sys
import time
import socket
import subprocess
from kazoo.client import KazooClient
from kazoo.recipe import watchers
from telnetlib import Telnet
import json

# load local isp zookeeper server ips
# load local isp PoP ips
config = json.loads(open(sys.argv[1]).read())

try:
    # use the ip addr of the eth interface Serval binds to
    servd_conn = Telnet(sys.argv[2], 9999)
    servd_conn.read_until('help\n')
except socket.error:
    print "Local servd not running, so we won't be able to get service info"

def get_local_service_table():
    # get a dictionary of
    # (next auth : next ip)
    servd_conn.write('s\r\n')
    # put a delay in
    servd_conn.read_some()
    servd_conn.write('h\r\n')
    all_service_lines = servd_conn.read_until('service table\n').split('\n')[3:-7]
    all_service_entries = [filter(None, line.split(' ')) for line in all_service_lines]
    taas_entries = [entry for entry in all_service_entries if entry[-3] not in ('0', 'none')]
    return {entry[-4]: entry[-3] for entry in taas_entries}

def register_service(auth, ip_addr, next_auth):
    return subprocess.call(['/taas/src/tools/servicetool', 'add', str(auth),
                            str(ip_addr), 'taas', str(next_auth)])

class CircuitStateWatcher():
    def __init__(self, zookeeperHosts='localhost:2181'):
        # might need to handle exceptions here
        # and try a list of zookeeper hosts
        self.zookeeper = KazooClient(zookeeperHosts)
        self.zookeeper.start()

        # use a hashtable to store all circuit states fetched from zookeeper
        self.circuitStates = {}
        # update the circuit state dictionary
        self._getCircuitState()

        # add to serval service table
        for auth in self.circuitStates.keys():
            next_ip = self.circuitStates[auth]['next_ip']
            next_auth = self.circuitStates[auth]['next_auth']
            register_service(auth, next_ip, next_auth)

        # set watcher on root node
        watchers.ChildrenWatch(self.zookeeper, '/circuit', self._circuitNodeWatcher)

    def _getCircuitState(self):
        # check if zookeeper circuit state node initialized
        if not self.zookeeper.exists('/circuit'):
            print 'no circuit has been established in zookeeper'
            print 'initialize empty circuit state in zookeeper'
            self.zookeeper.create('/circuit')

        # get circuit states
        authenticators = self.zookeeper.get_children('/circuit')

        for authenticator in authenticators:
            # transaction guarantees that
            # if /circuit/authenticator exists
            # then all three its children exist

            # get
            # return type is a tuple
            next_ip = self.zookeeper.get('/circuit/{0}/next_ip'.format(authenticator))
            next_ips = self.zookeeper.get('/circuit/{0}/next_ips'.format(authenticator))
            next_auth = self.zookeeper.get('/circuit/{0}/next_auth'.format(authenticator))

            # set watchers
            watchers.DataWatch(self.zookeeper, '/circuit/{0}/next_ip'.format(authenticator), self._nextIpWatcher)
            watchers.DataWatch(self.zookeeper, '/circuit/{0}/next_ips'.format(authenticator), self._nextIpsWatcher)
            watchers.DataWatch(self.zookeeper, '/circuit/{0}/next_auth'.format(authenticator), self._nextAuthWatcher)

            self.circuitStates[authenticator] = dict([
                                                    ('next_ip', next_ip[0]),
                                                    ('next_ips', next_ips[0]),
                                                    ('next_auth', next_auth[0])
                                                    ])

        print self.circuitStates


    def _circuitNodeWatcher(self, children):
        print '/circuit children updates'
        print 'children = ' + str(children)
        return

    def _nextIpWatcher(self, new_next_ip, stat, event):
        if event is None:
            return

        # new_next_ip is the new data value
        # stat is ZnodeStat
        # event is WatchedEvent(type='CHANGED', state='CONNECTED', path=u'/circuit/(auth)/next_ip')
        print 'next_ip has been changed in zookeeper'

        # find out the auth and old_next_ip
        auth = event.path.split('/')[2]
        next_auth = self.circuitStates[auth]['next_auth']
        old_next_ip = self.circuitStates[auth]['next_ip']
        
        # delete the old service table entry
        subprocess.call(['/taas/src/tools/servicetool', 'del', str(auth),
                            str(old_next_ip), 'taas', str(next_auth)])

        # fill in updated next_ip in service table
        register_service(auth, new_next_ip, next_auth)
        
        # update internal data structure
        self.circuitStates[auth]['next_ip'] = new_next_ip

        return

    def _nextIpsWatcher(self, data, stat, event):
        # print 'next_ips has been changed or created in zookeeper'
        return

    def _nextAuthWatcher(self, data, stat, event):
        print 'next_auth has been changed or created in zookeeper'
        return

    def serverForever(self):
        while True:
            time.sleep(1)

if __name__ == "__main__":
    circuitStateWatcher = CircuitStateWatcher(','.join(config['zookeeper']))
    circuitStateWatcher.serverForever()
