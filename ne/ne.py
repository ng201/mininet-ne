from mininet.node import Host
from mininet.node import UserSwitch

import os

class BaseRouter( Host ):
    """A basic router, i.e., a host with
       IP forwarding enabled."""

    def config( self, **params ):
        super( BaseRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def start( self ):
        """Routers should be started"""

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( BaseRouter, self ).terminate()


class LinuxRouter( BaseRouter ):
    """A router with lldp and snmp enabled"""

    def __init__( self, name, inNamespace=True, **params ):
        """File system is shared in Mininet, thus, we
           have to create some private directories to 
           store router specific data"""
        privateDirs = [ ( '/var/log', '/tmp/%(name)s.priv.dir/var/log' ),
                        ( '/var/run', '/tmp/%(name)s.priv.dir/var/run' ),
                        ( '/var/agentx', '/tmp/%(name)s.priv.dir/var/agentx' ),
                        ( '/var/lib/snmp', '/tmp/%(name)s.priv.dir/var/lib/snmp' ),
                          '/var/mn' ]
        options = { 'privateDirs' : privateDirs }
        options.update(params)
        super( LinuxRouter, self).__init__( name, inNamespace, **options )

    def start( self, **params):
        super( LinuxRouter, self).start()

        options = { 'agentXsocket' : '/var/agentx/master',
                    'agentAddress' : 161 }
        options.update(params)

        # create config file
        with open('/tmp/%s.priv.dir/snmpd.conf' % self.name, 'a') as cfg:

            # agent's address
            cfg.write('agentAddress %s\n' % params.get('agentAddress', 'udp:161,udp6:[::1]:161'))

            # access control
            access = params.get('agentAddress', ['.1.3.6.1.2.1.1',' .1.0.8802.1.1.2'])
            for a in access:
                cfg.write('view   systemonly  included   %s\n' % a)

            cfg.write('rocommunity public  default    -V systemonly\n')
            cfg.write('rocommunity6 public  default   -V systemonly\n')

            # system information
            cfg.write('sysLocation    %s\n' % params.get('sysLocation','Sitting on the Dock of the Bay at %s' % self.name))
            cfg.write('sysContact     %s\n' % params.get('sysLocation','%s <%s@example.org>' % (self.name, self.name)))
            cfg.write('sysName STRING %s\n' % params.get('sysLocation','%s' % self.name))

            cfg.write('sysServices    72\n')
            cfg.write('proc  mountd\n')
            cfg.write('proc  ntalkd    4\n')
            cfg.write('proc  sendmail 10 1\n')
            cfg.write('disk       /     10000\n')
            cfg.write('disk       /var  5%\n')
            cfg.write('includeAllDisks  10%\n')
            cfg.write('load   12 10 5\n')
            cfg.write('trapsink     localhost public\n')
            cfg.write('iquerySecName   internalUser\n')
            cfg.write('rouser          internalUser\n')
            cfg.write('defaultMonitors          yes\n')
            cfg.write('linkUpDownNotifications  yes\n')
            cfg.write('extend    test1   /bin/echo  Hello, world!\n')
            cfg.write('extend-sh test2   echo Hello, world! ; echo Hi there ; exit 35\n')

            # agentX
            cfg.write('master     agentx')

        socket = params.get('agentXsocket', '/var/agentx/master' )

        if(socket=='/var/agentx/master'):
            self.cmd('snmpd -C -c /tmp/%s.priv.dir/snmpd.conf & ' % self.name)
            self.cmd('lldpd -x &')
        else:
            p = int(socket)
            self.cmd('snmpd -C -c /tmp/%s.priv.dir/snmpd.conf -x tcp:127.0.0.1:' % self.name + str(p) + ' &')
            self.cmd('lldpd -x -X tcp:127.0.0.1:' + str(p) + ' &')


class SNMPSwitch( UserSwitch ):
    """A switch with snmp enabled"""

    def __init__( self, name, dpopts='--no-slicing', **params ):
        """File system is shared in Mininet, thus, we
           have to create some private directories to 
           store router specific data"""
        privateDirs = [ ( '/var/log', '/tmp/%(name)s.priv.dir/var/log' ),
                        ( '/var/run', '/tmp/%(name)s.priv.dir/var/run' ),
                        ( '/var/agentx', '/tmp/%(name)s.priv.dir/var/agentx' ),
                        ( '/var/lib/snmp', '/tmp/%(name)s.priv.dir/var/lib/snmp' ),
                          '/var/mn' ]
        options = { 'privateDirs' : privateDirs }
        options.update(params)
        options.update({'inNamespace': True})
        super( SNMPSwitch, self).__init__( name, dpopts, **options )

    def start( self, controllers, **params ):
        super( SNMPSwitch, self).start( controllers )

        options = { 'agentXsocket' : '/var/agentx/master',
                    'agentAddress' : 161 }
        options.update(params)

        # create config file
        with open('/tmp/%s.priv.dir/snmpd.conf' % self.name, 'a') as cfg:

            # agent's address
            cfg.write('agentAddress %s\n' % params.get('agentAddress', 'udp:161'))

            # access control
            access = params.get('agentAddress', ['.1.3.6.1.2.1.1',' .1.0.8802.1.1.2'])
            for a in access:
                cfg.write('view   systemonly  included   %s\n' % a)

            cfg.write('rocommunity public  default    -V systemonly\n')
            cfg.write('rocommunity6 public  default   -V systemonly\n')

            # system information
            cfg.write('sysLocation    %s\n' % params.get('sysLocation','Sitting on the Dock of the Bay at switch %s' % self.name))
            cfg.write('sysContact     %s\n' % params.get('sysLocation','%s <%s@example.org>' % (self.name, self.name)))
            cfg.write('sysName STRING %s\n' % params.get('sysLocation','%s' % self.name))

            cfg.write('sysServices    72\n')
            cfg.write('proc  mountd\n')
            cfg.write('proc  ntalkd    4\n')
            cfg.write('proc  sendmail 10 1\n')
            cfg.write('disk       /     10000\n')
            cfg.write('disk       /var  5%\n')
            cfg.write('includeAllDisks  10%\n')
            cfg.write('load   12 10 5\n')
            cfg.write('trapsink     localhost public\n')
            cfg.write('iquerySecName   internalUser\n')
            cfg.write('rouser          internalUser\n')
            cfg.write('defaultMonitors          yes\n')
            cfg.write('linkUpDownNotifications  yes\n')
            cfg.write('extend    test1   /bin/echo  Hello, world!\n')
            cfg.write('extend-sh test2   echo Hello, world! ; echo Hi there ; exit 35\n')

            # agentX
            cfg.write('master     agentx')

        socket = params.get('agentXsocket', '/var/agentx/master' )

        if(socket=='/var/agentx/master'):
            print 'starting snmp daemon'
            self.cmd('snmpd -C -c /tmp/%s.priv.dir/snmpd.conf & ' % self.name)
        else:
            p = int(socket)
            self.cmd('snmpd -C -c /tmp/%s.priv.dir/snmpd.conf -x tcp:127.0.0.1:' % self.name + str(p) + ' &')


class LLDPSwitch( SNMPSwitch ):
    """A switch with lldp and snmp enabled"""

    def __init__( self, name, dpopts='--no-slicing', **params ):
        super( LLDPSwitch, self).__init__( name, dpopts, **params )

    def start( self, controllers, ifaces, **params ):
        # some interface is given - check interfaces for existence
        if ifaces:
            # create the list of enabled interfaces
            ilist = ',' . join( [ '%s' % i for i in ifaces ] )
            # run lldpd
            self.cmd('lldpd -x -I ' + ilist + ' &')
        options = {}
        options.update(params)
        options.update({'agentXsocket' : '/var/agentx/master'})
        super( LLDPSwitch, self).start( controllers, **params )


class DNAT( BaseRouter ):
    """A router that can act as a DNAT"""

    def __save( self, rule ):
        """Saves the rule"""
        cmd = 'iptables -t nat -A PREROUTING ' + rule
        self.cmd(cmd)

    def __delete( self, rule ):
        """Deletes the rule"""
        cmd = 'iptables -t nat -D PREROUTING ' + rule
        self.cmd(cmd)

    def __prepare( self, rule ):
        """Converts the rule into a string acceptable 
           by the iptables command"""
        cmd = ""
        if(rule.get('iface','*')!='*'):
            cmd = cmd + ' -i ' + rule.get('iface')
        if(rule.get('proto','*')!='*'):
            cmd = cmd + ' -p ' + rule.get('proto')
        if(rule.get('src','*')!='*'):
            cmd = cmd + ' -s ' + rule.get('src')
        if(rule.get('dport','*')!='*'):
            cmd = cmd + ' --dport ' + str(rule.get('dport'))

        if(rule.get('todest','*')=='*'):
            cmd = cmd + ' -j REDIRECT --to-port ' + rule.get('toport','*')
        else:
            cmd = cmd + ' -j DNAT --to ' + rule.get('todest')
            if(rule.get('toport','*')!='*'):
                cmd = cmd + ':' + str(rule.get('toport'))
        return cmd

    def start( self, rules = [], *params ):
        """Starts the router with the configuration
           data exteracted from the params."""

        # set the rules for the chains
        self.cmd('iptables -P INPUT ACCEPT')
        self.cmd('iptables -P FORWARD ACCEPT')
        self.cmd('iptables -P OUTPUT ACCEPT')

        # collecting and saving rules
        for rule in rules:
            self.__save(self.__prepare(rule))
        for r in params:
            rule = {}
            rule.proto = r.get( 'proto', '*' )
            rule.iface = r.get( 'iface', '*' )
            rule.src = r.get( 'src', '*' )
            rule.dport = r.get( 'dport', '*' )
            rule.todest = r.get( 'todest', '*' )
            rule.toport = r.get( 'toport', '*' )
            self.__save(self.__prepare(rule))

    def stop( self ):
        # emptiing tables
        self.cmd('iptables -F')
        self.cmd('iptables -t nat -F')

class NetconfRouter( LinuxRouter ):
    """A router with netconf capabilities"""

#    def config( self, **params ):
#        super( NetconfRouter, self).config( **options )

    def start( self):
        # Initing lldp and snmp
        super( NetconfRouter, self).start()
        # Starting netconf
        """blablbablab"""

#    def terminate( self ):
#        super( NetconfRouter, self ).terminate()
