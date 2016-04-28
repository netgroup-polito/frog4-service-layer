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
        self.publish('frog:domain-description/0/0/0/', '{"frog-domain:informations":{"name":"UN2","type":"UN","management-address":"10.0.0.2:8080","frog-network-manager:informations":{"openconfig-interfaces:interfaces":{"openconfig-interfaces:interface":[{"name":"eth0","frog-interface-type":"core","openconfig-interfaces:subinterfaces":{"openconfig-interfaces:subinterface":[{"config":{"name":"eth0","enabled":true},"capabilities":{"gre":true}}]},"config":{"type":"ethernetCsmacd","enabled":true},"openconfig-if-ethernet:ethernet":{"frog-neighbor:neighbor":[{"domain-name":"isp","domain-type":"IP"}]}},{"name":"wlan0","frog-interface-type":"access","config":{"type":"ethernetCsmacd","enabled":true},"openconfig-if-ethernet:ethernet":{}}]}}}}')

    def unsubscribe(self, topic, scope):
        pass

    def on_error(self, code, msg):
        pass

conf = Configuration()
dd_client = DDClient('130.192.255.172:8080', conf.BROKER_ADDRESS, conf.DD_CUSTOMER, conf.DD_KEYFILE)
dd_client.start()
