'''
Created on 01 dic 2015
@author: stefanopetrangeli
'''
class DomainInfo(object):
    def __init__(self, name = None, interfaces=None, domain_id=None, _type=None, domain_ip=None, domain_port=None):
        self.name = name
        self.type = _type
        self.interfaces = interfaces or []
        self.domain_ip = domain_ip
        self.domain_port = domain_port
        self.domain_id = domain_id

    def parseDict(self, domaininfo_dict):
        self.name = domaininfo_dict['frog-domain:informations']['name']
        self.type = domaininfo_dict['frog-domain:informations']['type']
        management_address = domaininfo_dict['frog-domain:informations']['management-address']
        tmp = management_address.split(':')
        self.domain_ip = tmp[0]
        self.domain_port = tmp[1]

        if 'openconfig-interfaces:interfaces' in domaininfo_dict['frog-domain:informations']['frog-network-manager:informations']:
            for interface_dict in domaininfo_dict['frog-domain:informations']['frog-network-manager:informations']['openconfig-interfaces:interfaces']['openconfig-interfaces:interface']:
                interface = Interface()
                interface.parseDict(interface_dict)
                if interface.enabled is True:
                    self.interfaces.append(interface)

    def addInterface(self, interface):
        if type(interface) is Interface:
            self.interfaces.append(interface)
        else:
            raise TypeError("Tried to add an interface with a wrong type. Expected Interface, found "+type(interface))

    def getInterface(self, node, name):
        """
        :param node: the IP of the interface
        :param name: the name of the interface searched
        :return: the interface of the node specified having the passed name
        :rtype: Interface
        """
        for interface in self.interfaces:
            if interface.node == node and interface.name == name:
                return interface

    def getCoreInterfaceIfAny(self):
        """
        :return:
        :rtype: Interface
        """
        for interface in self.interfaces:
            if interface.type == 'core':
                return interface

class Interface(object):
    # Subinterfaces are ignored
    def __init__(self, node=None, name=None, _type=None, enabled=None, neighbors=None, gre=False, gre_tunnels=None, vlan=False, vlans_free=None):
        self.node = node
        self.name = name
        self.type = _type
        self.enabled = enabled
        self.gre = gre
        self.gre_tunnels = gre_tunnels or []
        self.vlan = vlan
        self.vlans_free = vlans_free or []
        self.neighbors = neighbors or []

    def parseDict(self, interface_dict):
        if '/' in interface_dict['name']:
            tmp = interface_dict['name']
            self.node = tmp.split('/')[0]
            self.name = tmp.split('/')[1]
        else:
            self.name = interface_dict['name']
        #if 'type' in interface_dict['config']:
        #    self.type = interface_dict['config']['type']
        if 'frog-interface-type' in interface_dict:
            self.type = interface_dict['frog-interface-type']
        self.enabled = interface_dict['config']['enabled']

        if 'openconfig-interfaces:subinterfaces' in interface_dict:
            for subinterface_dict in interface_dict['openconfig-interfaces:subinterfaces']['openconfig-interfaces:subinterface']:
                if subinterface_dict['config']['name'] == self.name:
                    if subinterface_dict['capabilities']['gre'] == True:
                        self.gre = True
                        if 'frog-if-gre:gre' in subinterface_dict:
                            for gre_dict in subinterface_dict['frog-if-gre:gre']:
                                gre_tunnel = GreTunnel()
                                gre_tunnel.parseDict(gre_dict)
                                self.gre_tunnels.append(gre_tunnel)

        if 'frog-neighbor:neighbor' in interface_dict['openconfig-if-ethernet:ethernet']:
            for neighbor_dict in interface_dict['openconfig-if-ethernet:ethernet']['frog-neighbor:neighbor']:
                neighbor = Neighbor()
                neighbor.parseDict(neighbor_dict)
                self.neighbors.append(neighbor)

        if 'openconfig-vlan:vlan' in interface_dict['openconfig-if-ethernet:ethernet']:
            self.vlan = True
            if 'openconfig-vlan:config' in interface_dict['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan']:
                vlan_config = interface_dict['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan']['openconfig-vlan:config']
                if vlan_config['interface-mode']=="TRUNK":
                    for vlan in vlan_config['trunk-vlans']:
                        self.vlans_free.append(vlan)

    def addNeighbor(self, neighbor):
        if type(neighbor) is Neighbor:
            self.neighbors.append(neighbor)
        else:
            raise TypeError("Tried to add a neighbor with a wrong type. Expected Neighbor, found "+type(neighbor))

    def addGreTunnel(self, gre_tunnel):
        if type(gre_tunnel) is GreTunnel:
            self.gre_tunnels.append(gre_tunnel)
        else:
            raise TypeError("Tried to add a gre tunnel with a wrong type. Expected GreTunnel, found "+type(gre_tunnel))

    def addVlan(self, vlan):
        self.vlans_free.append(vlan)

    def isAccess(self):
        return self.type == 'access'

    def isCore(self):
        return self.type == 'core'

    def isEgress(self):
        for neighbor in self.neighbors:
            if neighbor.domain_name == 'internet':
                return True
        return False

    def isLocal(self):
        for neighbor in self.neighbors:
            if neighbor.domain_name == 'isp':
                return True
        return False

class Neighbor(object):
    def __init__(self, domain_name=None, node=None, interface=None, domain_type=None):
        self.domain_name = domain_name
        self.node = node
        self.interface = interface
        self.domain_type = domain_type

    def parseDict(self, neighbor_dict):
        self.domain_name = neighbor_dict['domain-name']
        if 'remote-interface' in neighbor_dict:
            if '/' in neighbor_dict['remote-interface']:
                tmp = neighbor_dict['remote-interface']
                self.node = tmp.split('/')[0]
                self.interface = tmp.split('/')[1]
            else:
                self.interface = neighbor_dict['remote-interface']
        if 'domain-type' in neighbor_dict:
            self.domain_type = neighbor_dict['domain-type']

class GreTunnel(object):
    def __init__(self, name=None, local_ip=None, remote_ip=None, gre_key=None):
        self.name = name
        self.local_ip = local_ip
        self.remote_ip = remote_ip
        self.gre_key = gre_key

    def parseDict(self, gre_dict):
        self.name = gre_dict['config']['name']
        if 'local_ip' in gre_dict['options']:
            self.local_ip = gre_dict['options']['local_ip']
        if 'remote_ip' in gre_dict['options']:
            self.remote_ip = gre_dict['options']['remote_ip']
        if 'key' in gre_dict['options']:
            self.gre_key = gre_dict['options']['key']
