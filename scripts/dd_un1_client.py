from doubledecker.clientSafe import ClientSafe
from .config import Configuration


class DDClient(ClientSafe):

    def __init__(self, name, dealer_url, customer, keyfile):
        super().__init__(name, dealer_url, customer, keyfile)

    def on_data(self, dst, msg):
        pass

    def on_discon(self):
        pass

    def on_pub(self, src, topic, msg):
        pass

    def on_reg(self):
        self.subscribe("frog:domain-description", "/0/0/0/")
        self.publish('frog:domain-description/0/0/0/', '{"frog-domain:informations":{"type":"UN","name":"UN1","management-address":"10.0.0.4:8080","frog-network-manager:informations":{"openconfig-interfaces:interfaces":{"openconfig-interfaces:interface":[{"name":"eth0","frog-interface-type":"core","config":{"type":"ethernetCsmacd","enabled":true},"openconfig-interfaces:subinterfaces":{"openconfig-interfaces:subinterface":[{"config":{"name":"eth0","enabled":true},"capabilities":{"gre":true}}]},"openconfig-if-ethernet:ethernet":{"frog-neighbor:neighbor":[{"domain-name":"isp","domain-type":"IP"}]}},{"name":"eth4","frog-interface-type":"core","config":{"type":"ethernetCsmacd","enabled":true},"openconfig-interfaces:subinterfaces":{"openconfig-interfaces:subinterface":[{"config":{"name":"eth4","enabled":true},"capabilities":{"gre":false}}]},"openconfig-if-ethernet:ethernet":{"frog-neighbor:neighbor":[{"domain-name":"isp","domain-type":"IP"}]}},{"name":"eth1","frog-interface-type":"core","config":{"type":"ethernetCsmacd","enabled":true},"openconfig-interfaces:subinterfaces":{"openconfig-interfaces:subinterface":[{"config":{"name":"eth1","enabled":true},"capabilities":{"gre":true}}]},"openconfig-if-ethernet:ethernet":{"frog-neighbor:neighbor":[{"domain-name":"internet","domain-type":"IP"}]}}]}}}}')

    def unsubscribe(self, topic, scope):
        pass

    def on_error(self, code, msg):
        pass


conf = Configuration()
dd_client = DDClient('130.192.255.171:8080', conf.BROKER_ADDRESS, conf.DD_CUSTOMER, conf.DD_KEYFILE)
dd_client.start()
