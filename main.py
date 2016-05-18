"""
Created on Oct 1, 2014

@author: fabiomignini
@author: gabrielecastellano
"""

import falcon
import logging
import os
import inspect

from threading import Thread
from service_layer_application_core.config import Configuration
from service_layer_application_core.service_layer_application import ServiceLayer
from service_layer_application_core.dd_client import DDClient

conf = Configuration()

# set log level
if conf.DEBUG is True:
    log_level = logging.DEBUG
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
elif conf.VERBOSE is True:
    log_level = logging.INFO
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
else:
    log_level = logging.WARNING

# format = '%(asctime)s %(filename)s %(funcName)s %(levelname)s %(message)s'
log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s:%(lineno)s'

logging.basicConfig(filename=conf.LOG_FILE, level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.debug("Service Layer Starting")
print("Welcome to the User-oriented Service Layer Application")

# Falcon starts
app = falcon.API()
logging.info("Starting Service Layer application")

serviceLayer = ServiceLayer()
app.add_route('/service-layer', serviceLayer)
app.add_route('/service-layer/{mac_address}', serviceLayer)

logging.info("Falcon Successfully started")

# start the dd client to receive information about domains
base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
dd_client = DDClient(conf.DD_NAME, conf.BROKER_ADDRESS, conf.DD_CUSTOMER, conf.DD_KEYFILE)
thread = Thread(target=dd_client.start)
thread.start()

logging.info("DoubleDecker Client Successfully started")
