import os
import argparse

from subprocess import call
from service_layer_application_core.config import Configuration

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument(
      '-d',
      "--conf_file",
      nargs='?',
      help='Configuration file'
)

args = parser.parse_args()

# set configuration file
if args.conf_file:
    os.environ.setdefault("FROG4_SL_CONF", args.conf_file)

conf = Configuration()
ip = conf.SERVICE_LAYER_IP
port = conf.SERVICE_LAYER_PORT
address = str(ip) + ":" + str(port)

call("gunicorn -b " + address + " -t 500 main:app", shell=True)
