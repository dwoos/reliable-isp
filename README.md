reliable-isp
============

Reliable ISP project for CSE 552

Demo
----

* How to establish circuit from client - ISP 1 - ISP 2 - ... - ISP n - server?

client: runs circuitc.py ISP1 ISP2 ... ISPn server to establish entire circuit

transit ISP 1: runs circuitd.py to respond to client circuitc create circuit request
transit ISP 2: runs circuitd.py to respond to client circuitc create circuit request
...
transit ISP n: runs circuitd.py to respond to client circuitc create circuit request

* How to emulate Serval forwarding packet?

client: runs send.py authenticator ISP1 message

transit ISP: runs forwarderd.py

server runs udp-echo-server.py

* Configurations
    - each ISP can configure isp.json file to specify
        - zookeeper server at this PoP
        - all the PoP forwarderd servers

* How to use Watcherd?
    - each Serval forwarder runs Watcherd to monitor changes in circuit state
    - any changes/updates would trigger callbacks that updates the Serval forwarding table
