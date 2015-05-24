#!/usr/bin/python
#import re
#import sys

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Host, Node
from mininet.node import UserSwitch, Controller, RemoteController
from mininet.link import TCLink, Intf
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info, error
from mininet.util import quietRun

from ne.ne import BaseRouter, LinuxRouter, DNAT, LLDPSwitch, SNMPSwitch

def createNet():
    """One network, two controllers."""

    net = Mininet( )

    info( '*** Adding controllers\n' )
    c1 = net.addController('c1',controller=RemoteController,ip='172.17.42.1',port=6634)
    c2 = net.addController('c2',controller=RemoteController,ip='172.17.42.1',port=6635)

    info( '*** Adding switches\n' )
    s13 = net.addSwitch('s13',cls=SNMPSwitch);
    s12 = net.addSwitch('s12',cls=UserSwitch);
    s11 = net.addSwitch('s11',cls=LLDPSwitch);

    s23 = net.addSwitch('s23',cls=LLDPSwitch);
    s22 = net.addSwitch('s22',cls=UserSwitch);
    s21 = net.addSwitch('s21',cls=SNMPSwitch);

    info( '*** Adding links\n' )
    net.addLink(s11,s12,cls=TCLink,**dict(bw=1, delay='0ms', loss=0, max_queue_size=1000, use_htb=True));
    net.addLink(s12,s13,cls=TCLink,**dict(bw=1, delay='0ms', loss=0, max_queue_size=1000, use_htb=True));
    net.addLink(s21,s22,cls=TCLink,**dict(bw=1, delay='0ms', loss=0, max_queue_size=1000, use_htb=True));
    net.addLink(s22,s23,cls=TCLink,**dict(bw=1, delay='0ms', loss=0, max_queue_size=1000, use_htb=True));

    net.addLink(s13,s21,cls=TCLink,**dict(bw=1, delay='0ms', loss=0, max_queue_size=1000, use_htb=True));

    info( '\n' )
    info( '*** Adding hosts\n' )
    h1 = net.addHost('h1', ip='10.0.1.1/24' );
    h2 = net.addHost('h2', ip='10.0.2.1/24' );

    info( '*** Adding routers\n' )
    j1 = net.addHost('j1', cls=LinuxRouter, ip='10.0.1.201/24' );
    j2 = net.addHost('j2', cls=LinuxRouter, ip='10.0.2.201/24' );

    net.addLink(j1, h1, intfName1='j1-eth1', params1={ 'ip' : '10.0.1.201/24' });
    net.addLink(j2, h2, intfName1='j2-eth1', params1={ 'ip' : '10.0.2.201/24' });

    net.addLink(j1, s11, intfName1='j1-eth2', params1={ 'ip' : '10.0.200.201/24' });
    net.addLink(j2, s23, intfName1='j2-eth2', params1={ 'ip' : '10.0.200.202/24' });

    info( '*** Creating DNAT\n' )

    #root = Node('root', inNamespace=False, ip='10.200.1.201/24')
    root = net.addHost( 'root', cls=DNAT, inNamespace=False, ip='10.200.1.1/24')

    info( '*** Connecting routers to NAT\n' )
    net.addLink(root, j1, intfName1='eth1', intfName2='j1-eth3', params1={ 'ip' : '10.200.1.1/24' }, params2={ 'ip' : '10.200.1.201/24' });
    net.addLink(root, j2, intfName1='eth2', intfName2='j2-eth3', params1={ 'ip' : '10.200.2.1/24' }, params2={ 'ip' : '10.200.2.201/24' });

    net.addLink(root, s11, intfName1='eth3', params1={ 'ip' : '10.200.3.1/24' }, params2={ 'ip' : '10.200.3.201/24' });
    net.addLink(root, s23, intfName1='eth4', params1={ 'ip' : '10.200.4.1/24' }, params2={ 'ip' : '10.200.4.201/24' });
    net.addLink(root, s13, intfName1='eth5', params1={ 'ip' : '10.200.5.1/24' }, params2={ 'ip' : '10.200.5.201/24' });
    net.addLink(root, s21, intfName1='eth6', params1={ 'ip' : '10.200.6.1/24' }, params2={ 'ip' : '10.200.6.201/24' });

    info( '*** Starting network\n')
    net.build()

    c1.start()
    c2.start()
    s11.start( [ c1 ], ['s11-eth2'] )
    s12.start( [ c1 ] )
    s13.start( [ c1 ] )
    s21.start( [ c2 ] )
    s22.start( [ c2 ] )
    s23.start( [ c2 ], ['s23-eth2'] )

    #info( '*** Starting NAT\n')
    #startNAT( root )

    info( '*** Adding default routes\n' )

    j1.cmd('route add -net 10.0.0.0 netmask 255.255.0.0 j1-eth2')
    j2.cmd('route add -net 10.0.0.0 netmask 255.255.0.0 j2-eth2')

    #j1.cmd('route add -net 10.200.0.0 netmask 255.255.0.0 j1-eth3')
    #j2.cmd('route add -net 10.200.0.0 netmask 255.255.0.0 j2-eth3')
    #j3.cmd('route add -net 10.200.0.0 netmask 255.255.0.0 j3-eth3')
    j1.cmd('route add default gw 10.200.1.1')
    j2.cmd('route add default gw 10.200.2.1')

    s11.cmd('route add default gw 10.200.3.1')
    s23.cmd('route add default gw 10.200.4.1')
    s13.cmd('route add default gw 10.200.5.1')
    s21.cmd('route add default gw 10.200.6.1')

    h1.cmd('route add default gw 10.0.1.251')
    h2.cmd('route add default gw 10.0.2.251')

    root.cmd('route add -net 10.0.1.0 netmask 255.255.255.0 eth1')
    root.cmd('route add -net 10.0.2.0 netmask 255.255.255.0 eth2')

    print "*** Routers are running and should have internet connectivity"
    print "*** Type 'exit' or control-D to shut down network"

    print "*** Starting DNAT"
    root.start([
                {'iface' : 'eth0', 'proto' : 'udp', 'dport' : 30001, 'toport': 161, 'todest': '10.200.1.201'},
                {'iface' : 'eth0', 'proto' : 'udp', 'dport' : 30002, 'toport': 161, 'todest': '10.200.2.201'},
                {'iface' : 'eth0', 'proto' : 'udp', 'dport' : 31001, 'toport': 161, 'todest': '10.200.3.201'},
                {'iface' : 'eth0', 'proto' : 'udp', 'dport' : 31002, 'toport': 161, 'todest': '10.200.4.201'},
                {'iface' : 'eth0', 'proto' : 'udp', 'dport' : 32001, 'toport': 161, 'todest': '10.200.5.201'},
                {'iface' : 'eth0', 'proto' : 'udp', 'dport' : 32002, 'toport': 161, 'todest': '10.200.6.201'},
               ])
    root.cmd('iptables -t nat -A POSTROUTING -d 172.17.42.1 -o eth0 -j MASQUERADE ');

    print "*** Starting routers"
    j1.start()
    j2.start()

    info( '*** Running CLI\n' )
    CLI( net )

    info( '*** Stopping network' )
    #stopNAT( root )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    createNet()
