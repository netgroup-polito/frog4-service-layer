import argparse
import inspect
import os

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
        self.publish('frog:domain-description/0/0/0/', json_info)

    def unsubscribe(self, topic, scope):
        pass

    def on_error(self, code, msg):
        pass

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "name",
    help='name used in double decker (use an IP address for uniqueness)'
)
parser.add_argument(
    "info_file",
    help='file containing the json with the domain informations'
)

args = parser.parse_args()

base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])).rpartition('/')[0]
json_info = open(base_folder + "/" + args.info_file).read()
print(json_info)

conf = Configuration()
dd_client = DDClient(args.name, conf.BROKER_ADDRESS, conf.DD_CUSTOMER, conf.DD_KEYFILE)
dd_client.start()
