import argparse
import json
import logging

from service_layer_application_core.client_graph_manager import ClientGraphManager
from service_layer_application_core.controller import ServiceLayerController
from service_layer_application_core.sql.user import User
from service_layer_application_core.user_authentication import UserAuthentication
from service_layer_application_core.validate_request import RequestValidator

# set log level
log_level = logging.DEBUG

log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s:%(lineno)s'

logging.basicConfig(filename='delete_script.log', level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.debug("Service Layer Starting")

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "username",
    help='Username of the graph owner'
)
parser.add_argument(
    "mac",
    help='Mac of the user device'
)

args = parser.parse_args()

try:
    mac_address = args.mac
    user_model = User().getUser(args.username)
    user_data = UserAuthentication().authenticateUserFromCredentials(
        user_model.name,
        user_model.password,
        User().getTenantName(user_model.tenant_id)
    )
    graph_manager = ClientGraphManager(user_data)
    graph_manager.delete_endpoint_from_user_device_if_last(mac_address)

    # Now, it initialize a new controller instance to handle the request
    controller = ServiceLayerController(user_data)
    controller.delete(mac_address=mac_address, nffg=graph_manager.nffg)
except Exception as err:
    logging.exception(err)
