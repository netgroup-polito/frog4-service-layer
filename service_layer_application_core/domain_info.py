"""
Created on 01 dic 2015

@author: stefanopetrangeli
"""


class DomainInfo(object):
    def __init__(self, name=None, interfaces=None, domain_id=None, _type=None):
        self.name = name
        self.type = _type
        self.interfaces = interfaces or []
        self.domain_id = domain_id

    def parseDict(self, domain_info_dict):
        self.name = domain_info_dict['netgroup-domain:informations']['name']
        self.type = domain_info_dict['netgroup-domain:informations']['type']
        if 'openconfig-interfaces:interfaces' in domain_info_dict['netgroup-domain:informations'][
                'netgroup-network-manager:informations']:
            for interface_dict in \
                    domain_info_dict['netgroup-domain:informations']['netgroup-network-manager:informations'][
                        'openconfig-interfaces:interfaces']['openconfig-interfaces:interface']:
                interface = Interface()
                interface.parseDict(interface_dict)
                if interface.enabled is True:
                    self.interfaces.append(interface)

    def addInterface(self, interface):
        if type(interface) is Interface:
            self.interfaces.append(interface)
        else:
            raise TypeError("Tried to add an interface with a wrong type. Expected Interface, found " + type(interface))

    def getInterface(self, node, name):
        for interface in self.interfaces:
            if interface.node == node and interface.name == name:
                return interface


class Interface(object):
    # Subinterfaces are ignored
    def __init__(self, node=None, name=None, _type=None, enabled=None, neighbors=None, gre=False, gre_tunnels=None,
                 vlan=False, vlans_free=None):
        # Interface is composed of node and name
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
        tmp = interface_dict['name']
        self.node = tmp.split('/')[0]
        self.name = tmp.split('/')[1]
        if 'type' in interface_dict['config']:
            self.type = interface_dict['config']['type']
        self.enabled = interface_dict['config']['enabled']

        if 'openconfig-interfaces:subinterfaces' in interface_dict:
            for subinterface_dict in interface_dict['openconfig-interfaces:subinterfaces'][
                    'openconfig-interfaces:subinterface']:
                if subinterface_dict['config']['name'] == self.name:
                    if subinterface_dict['capabilities']['gre']:
                        self.gre = True
                        if 'netgroup-if-gre:gre' in subinterface_dict:
                            for gre_dict in subinterface_dict['netgroup-if-gre:gre']:
                                gre_tunnel = GreTunnel()
                                gre_tunnel.parseDict(gre_dict)
                                self.gre_tunnels.append(gre_tunnel)

        if 'netgroup-neighbor:neighbor' in interface_dict['openconfig-if-ethernet:ethernet']:
            for neighbor_dict in interface_dict['openconfig-if-ethernet:ethernet']['netgroup-neighbor:neighbor']:
                neighbor = Neighbor()
                neighbor.parseDict(neighbor_dict)
                self.neighbors.append(neighbor)

        if 'openconfig-vlan:vlan' in interface_dict['openconfig-if-ethernet:ethernet']:
            self.vlan = True
            if 'openconfig-vlan:config' in interface_dict['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan']:
                vlan_config = interface_dict['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan'][
                    'openconfig-vlan:config']
                if vlan_config['interface-mode'] == "TRUNK":
                    for vlan in vlan_config['trunk-vlans']:
                        self.vlans_free.append(vlan)

    def addNeighbor(self, neighbor):
        if type(neighbor) is Neighbor:
            self.neighbors.append(neighbor)
        else:
            raise TypeError("Tried to add a neighbor with a wrong type. Expected Neighbor, found " + type(neighbor))

    def addGreTunnel(self, gre_tunnel):
        if type(gre_tunnel) is GreTunnel:
            self.gre_tunnels.append(gre_tunnel)
        else:
            raise TypeError(
                "Tried to add a gre tunnel with a wrong type. Expected GreTunnel, found " + type(gre_tunnel))

    def addVlan(self, vlan):
        self.vlans_free.append(vlan)


class Neighbor(object):
    def __init__(self, domain_name=None, node=None, interface=None):
        self.domain_name = domain_name
        self.node = node
        self.interface = interface

    def parseDict(self, neighbor_dict):
        self.domain_name = neighbor_dict['domain']
        if 'interface' in neighbor_dict:
            tmp = neighbor_dict['interface']
            self.node = tmp.split('/')[0]
            self.interface = tmp.split('/')[1]


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
