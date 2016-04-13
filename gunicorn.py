from subprocess import call
from service_layer_application_core.config import Configuration

conf = Configuration()
ip = conf.SERVICE_LAYER_IP
port = conf.SERVICE_LAYER_PORT
address = str(ip) + ":" + str(port)

call("gunicorn -b " + address + " -t 500 main:app", shell=True)
