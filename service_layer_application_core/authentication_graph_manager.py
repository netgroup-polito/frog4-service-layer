"""
Created on Apr 14, 2016

@author: gabrielecastellano
"""
import logging

from service_layer_application_core.common.user_session import UserSession
from service_layer_application_core.config import Configuration
from service_layer_application_core.controller import ServiceLayerController
from service_layer_application_core.nffg_manager import NFFG_Manager
from service_layer_application_core.orchestrator_rest import GlobalOrchestrator
from service_layer_application_core.sql.user import User
from service_layer_application_core.user_authentication import UserData
from .domain_info import DomainInfo


class AuthGraphManager:

    orchestrator_ip = Configuration().ORCH_IP
    orchestrator_port = Configuration().ORCH_PORT
    # TODO take these from db
    admin_id = 0
    admin_name = 'admin'
    admin_password = 'qwerty'
    admin_tenant = 'admin'

    def __init__(self):
        self.graph_instantiated = False
        self.current_domain = DomainInfo()

    def instantiate(self, domain_info):
        if domain_info.type == "UN":
            # try to instantiate an auth graph on this domain
            try:
                logging.debug("Trying to instantiate the authentication graph on domain '" + domain_info.name + "'")
                user_data = UserData(self.admin_name, self.admin_password, self.admin_tenant)
                controller = ServiceLayerController(user_data)
                # TODO should we specify the domain name or not?
                controller.put(mac_address=None)
                logging.info("Authentication graph correctly instantiated on domain '" + domain_info.name + "'")
                print("Instantiated authentication graph")
            except Exception as err:
                logging.error("Failed to instantiate authentication graph on this domain")
                logging.error(str(err))

    def is_instantiated(self):
        # TODO substitute this with a controller.get when the get status will be implemented on the UN
        # ask to orchestrator if the authentication graph is instantiated
        user_nffg_file = User().getServiceGraph(self.admin_name)
        nffg = NFFG_Manager.getNF_FGFromFile(user_nffg_file)
        user_data = UserData(self.admin_name, self.admin_password, self.admin_tenant)
        orchestrator = GlobalOrchestrator(user_data, self.orchestrator_ip, self.orchestrator_port)
        return UserSession(self.admin_id, None).checkSession(nffg.id, orchestrator)
