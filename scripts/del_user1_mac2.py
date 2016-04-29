import json
import logging

from service_layer_application_core.client_graph_manager import ClientGraphManager
from service_layer_application_core.controller import ServiceLayerController
from service_layer_application_core.user_authentication import UserAuthentication
from service_layer_application_core.validate_request import RequestValidator

# set log level
log_level = logging.DEBUG

log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s:%(lineno)s'

logging.basicConfig(filename='script5.log', level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.debug("Service Layer Starting")

try:
    mac_address = '22:22:22:bb:bb:bb'
    user_data = UserAuthentication().authenticateUserFromCredentials('user1', 'password1', 'public')
    graph_manager = ClientGraphManager(user_data)
    graph_manager.delete_endpoint_from_user_device_if_last(mac_address)

    # Now, it initialize a new controller instance to handle the request
    controller = ServiceLayerController(user_data)
    controller.delete(mac_address=mac_address, nffg=graph_manager.nffg)
except Exception as err:
    logging.exception(err)
