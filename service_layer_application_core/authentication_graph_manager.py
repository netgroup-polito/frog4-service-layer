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
from service_layer_application_core.sql.domains_info import DomainInformation
from service_layer_application_core.sql.user import User
from service_layer_application_core.sql.domain import Domain
from service_layer_application_core.user_authentication import UserData
from nffg_library.nffg import NF_FG, EndPoint

from .domain_info import DomainInfo


class AuthGraphManager:

    orchestrator_ip = Configuration().ORCH_IP
    orchestrator_port = Configuration().ORCH_PORT

    def __init__(self):
        self.graph_instantiated = False
        self.current_domain_id = 0
        admin_model = User().getUser(Configuration().ADMIN_NAME)
        self.admin_id = admin_model.id
        self.admin_name = admin_model.name
        self.admin_password = admin_model.password
        self.admin_tenant = User().getTenantName(admin_model.tenant_id)

    def instantiate(self, domain_info=None):
        """
        Try to instantiate the authentication graph

        :param domain_info: if specified, the SL will ask to the Orchestrator to instantiate it
        on this particular domain
        :return:
        :type domain_info: DomainInfo
        """

        if domain_info is not None:
            domain_name = domain_info.name
            logging.debug("Trying to instantiate the authentication graph on domain '" + domain_info.name + "'...")
        else:
            domain_name = None
            logging.debug("Trying to instantiate the authentication graph on the default domain...")

        if (domain_info is None) or (domain_info.type == "UN"):
            try:
                user_data = UserData(self.admin_name, self.admin_password, self.admin_tenant)
                controller = ServiceLayerController(user_data)
                controller.put(domain_name=domain_name)
                logging.info("Authentication graph correctly instantiated")
                print("Authentication graph instantiated")
                if domain_name is not None:
                    self.current_domain_id = domain_info.domain_id
            except Exception as err:
                logging.error("Failed to instantiate authentication graph.")
                logging.exception(err)

    def update(self, nffg):
        """
        update the currently instantiated authentication graph
        :param nffg: the new nffg
        :return:
        """
        try:
            logging.debug("Updating the instantiated authentication graph...")
            current_domain = Domain().get_domain(self.current_domain_id)
            user_data = UserData(self.admin_name, self.admin_password, self.admin_tenant)
            controller = ServiceLayerController(user_data)
            controller.put(domain_name=current_domain.name, nffg=nffg)
            logging.info("Authentication graph correctly updated")
        except Exception as err:
            logging.error("Failed to update the authentication graph.")
            logging.exception(err)

    def is_instantiated(self):
        """
        asks to the global orchestrator if the authentication graph is instantiated.

        :return: returns true if is yet instantiated somewhere.
        :rtype: bool
        """
        # TODO substitute this with a controller.get when the get status will be implemented on the UN
        # ask to orchestrator if the authentication graph is instantiated
        user_nffg_file = User().getServiceGraph(self.admin_name)
        nffg = NFFG_Manager.getNF_FGFromFile(user_nffg_file)
        user_data = UserData(self.admin_name, self.admin_password, self.admin_tenant)
        orchestrator = GlobalOrchestrator(user_data, self.orchestrator_ip, self.orchestrator_port)
        return UserSession(self.admin_id, None).checkSession(nffg.id, orchestrator)

    def get_current_instance(self):
        """
        requests and returns the currently instantiated authentication graph nffg

        :return: the authentication graph currently instantiated
        :rtype: NF_FG
        """
        try:
            user_data = UserData(self.admin_name, self.admin_password, self.admin_tenant)
            controller = ServiceLayerController(user_data)
            nffg = controller.get_nffg()
            return nffg
        except Exception as err:
            logging.error("Failed to take the currently instantiated authentication graph from orchestrator.")
            logging.exception(err)

    def add_remote_end_point(self, remote_domain_info):
        """
        Add a new remote end-point to the currently instantiated authentication graph,
        and configure the new domain with a graph with a specular end-point
        :param remote_domain_info: the new domain to attach
        :return:
        :type remote_domain_info: DomainInfo
        """

        # get current instance of nffg
        current_domain_name = Domain().get_domain(self.current_domain_id).name
        nffg = self.get_current_instance()
        if nffg is not None:
            if remote_domain_info.name != current_domain_name:
                logging.debug("Adding end point to auth-graph for the new domain: '" + remote_domain_info.name + "'")
                for interface in remote_domain_info.interfaces:
                    # TODO should do this only if it's the internet interface

                    # get the ip assigned to the interface of the 'auth-graph-domain' where
                    #  remote end-points should be attached
                    current_domain_ingress_ip = DomainInformation()\
                        .get_node_by_interface(self.current_domain_id, Configuration().REMOTE_INGRESS_PORT)
                    # create a new end-point
                    end_point = EndPoint(
                        _id=nffg.getNextAvailableEndPointId(),
                        name=Configuration().REMOTE_USER_INGRESS,
                    )
                    nffg.addEndPoint(end_point)
                    # add this remote connection in db (currently is supported a gre-endpoint)
                    current_domain_info = DomainInformation.get_domain_info_by_interface(
                        self.current_domain_id,
                        Configuration().REMOTE_INGRESS_PORT
                    )
                    DomainInformation.add_domain_gre(
                        domain_gre_id=int(end_point.id),
                        domain_name=current_domain_name,
                        domain_info_id=current_domain_info.id,
                        local_ip=current_domain_ingress_ip,
                        remote_ip=interface.node,
                        gre_key=remote_domain_info.domain_id
                    )
                    logging.debug("Endpoint '" + end_point.id + "' created")
                    # insert two flow rules to connect the end point to the switch NF
                    # TODO do it!
                    # now instantiate a graph with simply a remote end-point into the new domain
                    # TODO do it!
                    break

                # update the authentication graph
                logging.debug("Adding the new end point to the authentication graph...")
                self.update(nffg)
            else:
                # TODO this is the domain with the auth-graph! Should we add also its interfaces as end-points?
                pass
