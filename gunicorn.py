from subprocess import call
from service_layer_application_core.config import Configuration

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument(
      '-d',
      "--conf-file",
      nargs='?',
      help='Configuration file'
)

args = parser.parse_args()

# set configuration file
if args.file:
  Configuration.config_file = args.file

conf = Configuration()
ip = conf.SERVICE_LAYER_IP
port = conf.SERVICE_LAYER_PORT
address = str(ip) + ":" + str(port)

call("gunicorn -b " + address + " -t 500 main:app", shell=True)
