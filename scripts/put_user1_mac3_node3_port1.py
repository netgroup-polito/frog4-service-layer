import json
import logging

from service_layer_application_core.client_graph_manager import ClientGraphManager
from service_layer_application_core.controller import ServiceLayerController
from service_layer_application_core.user_authentication import UserAuthentication
from service_layer_application_core.validate_request import RequestValidator

# set log level
log_level = logging.DEBUG

log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s:%(lineno)s'

logging.basicConfig(filename='script3.log', level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.debug("Service Layer Starting")

try:
    user_data = UserAuthentication().authenticateUserFromCredentials('user1', 'password1', 'public')
    logging.debug("Authenticated user: " + user_data.username)
    # Now, it initialize a new controller instance to handle the request
    controller = ServiceLayerController(user_data)
    request_dict = json.loads('{"session":{"device":{"mac":"33:33:33:cc:cc:cc", "port":"eth5"}}}')
    RequestValidator.validate(request_dict)
    if 'device' in request_dict['session']:
        # add a new endpoint to the graph for this device if it came from a new port
        graph_manager = ClientGraphManager(user_data)
        graph_manager.prepare_egress_end_point()
        device_endpoint_id = graph_manager.add_endpoint_from_auth_switch_interface(
            request_dict['session']['device']['port']
        )
        # send request to controller
        controller.put(
            mac_address=request_dict['session']['device']['mac'],
            nffg=graph_manager.nffg,
            device_endpoint_id=device_endpoint_id
        )
    else:
        controller.put()
except Exception as err:
    logging.exception(err)
