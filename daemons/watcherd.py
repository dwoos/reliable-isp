import sys
import time
import socket
import subprocess
from kazoo.client import KazooClient
from kazoo.recipe import watchers
from telnetlib import Telnet

try:
    servd_conn = Telnet('localhost', 9999)
    servd_conn.read_until('help\n')
except socket.error:
    print "Local servd not running, so we won't be able to get service info"

def get_local_service_table():
    servd_conn.write('s\r\n')
    # put a delay in
    servd_conn.read_some()
    servd_conn.write('h\r\n')
    all_service_lines = servd_conn.read_until('service table\n').split('\n')[3:-7]
    all_service_entries = [filter(None, line.split(' ')) for line in all_service_lines]
    taas_entries = [entry for entry in all_service_entries if entry[-2] not in ('0', 'none')]
    return {entry[-2]: entry[-1] for entry in taas_entries}

def register_service(auth, ip_addr):
    return subprocess.call(['/root/taas/src/tools/servicetool', 'add', auth,
                            ip_addr, 'taas', auth])


class CircuitStateWatcher():
    def __init__(self, zookeeperHosts='localhost:2181'):
        # might need to handle exceptions here
		# and try a list of zookeeper hosts
		self.zookeeper = KazooClient(zookeeperHosts)
		self.zookeeper.start()

		# use a hashtable to store all circuit states fetched from zookeeper
		self.circuitStates = {}
		self._getCircuitState()

    def _getCircuitState(self):
		# check if zookeeper circuit state node initialized
		if not self.zookeeper.exists('/circuit'):
			print 'no circuit has been established in zookeeper'
			print 'initialize empty circuit state in zookeeper'
			zookeeper.create('/circuit')


		# get circuit states
		authenticators = self.zookeeper.get_children('/circuit')

		# set watcher on root node
		watchers.ChildrenWatch(self.zookeeper, '/circuit', self._circuitNodeWatcher)

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

    def _nextIpWatcher(self, data, stat, event):
    	# data is the new data value
    	# stat is ZnodeStat
    	# event is WatchedEvent(type='CHANGED', state='CONNECTED', path=u'/circuit/(auth)/next_ip')
        print 'next_ip has been changed in zookeeper'
        return

    def _nextIpsWatcher(self, data, stat, event):
        print 'next_ips has been changed or created in zookeeper'
        return

    def _nextAuthWatcher(self, data, stat, event):
        print 'next_auth has been changed or created in zookeeper'
        return

    def serverForever(self):
        while True:
            time.sleep(1)

if __name__ == "__main__":
    circuitStateWatcher = CircuitStateWatcher()
    circuitStateWatcher.serverForever()
