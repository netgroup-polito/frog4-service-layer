"""
Created on Apr 14, 2016

@author: gabrielecastellano
"""
import json
import logging

from service_layer_application_core.common.user_session import UserSession
from service_layer_application_core.config import Configuration
from service_layer_application_core.nffg_manager import NFFG_Manager
from service_layer_application_core.orchestrator_rest import GlobalOrchestrator
from service_layer_application_core.sql.end_point import EndPointDB
from service_layer_application_core.sql.graph import Graph
from service_layer_application_core.sql.session import Session
from service_layer_application_core.sql.user import User
from service_layer_application_core.sql.domain import Domain
from service_layer_application_core.user_authentication import UserData
from nffg_library.nffg import NF_FG, EndPoint, FlowRule, Port, Match, Action

from .domain_info import DomainInfo


class ISPGraphManager:
    orchestrator_ip = Configuration().ORCH_IP
    orchestrator_port = Configuration().ORCH_PORT

    def __init__(self):
        isp_model = User().getUser(Configuration().ISP_USERNAME)
        self.isp_id = isp_model.id
        self.isp_name = isp_model.name
        self.isp_password = isp_model.password
        self.isp_tenant = User().getTenantName(isp_model.tenant_id)
        self.current_domain_id = None
        # get current instance of isp service-graph
        if Session().checkSession(self.isp_id):
            session_id = Session().get_active_user_session(self.isp_id).id
            self.current_domain_id = Graph().get_last_graph(session_id).domain_id

    def instantiate_isp_graph(self, domain_info=None):
        """
        Try to instantiate the isp graph

        :param domain_info: if specified, the SL will ask to the Orchestrator to instantiate it
        on this particular domain
        :return:
        :type domain_info: DomainInfo
        """

        if domain_info is not None:
            domain_name = domain_info.name
            logging.debug("Trying to instantiate the isp graph on domain '" + domain_info.name + "'...")
        else:
            domain_name = None
            logging.debug("Trying to instantiate the isp graph on the default domain...")

        if (domain_info is None) or (domain_info.type == "UN"):

            # get the isp graph
            nffg = NFFG_Manager.getNF_FGFromFile('isp_graph.json')

            # prepare the egress end point
            self._prepare_egress_end_point(nffg, domain_info)
            # send to controller
            try:
                user_data = UserData(self.isp_name, self.isp_password, self.isp_tenant)
                from service_layer_application_core.controller import ServiceLayerController
                controller = ServiceLayerController(user_data)
                controller.put(domain_name=domain_name, nffg=nffg)
                logging.info("Isp graph correctly instantiated")
                print("Isp graph instantiated")
                if domain_name is not None:
                    self.current_domain_id = domain_info.domain_id
                else:
                    # TODO this is wronged, i should ask to the orchestrator
                    session_id = Session().get_active_user_session(self.isp_id).id
                    self.current_domain_id = Graph().get_last_graph(session_id).domain_id
            except Exception as err:
                print("Failed to instantiate isp graph.")
                logging.error("Failed to instantiate isp graph.")
                logging.exception(err)

    def is_instantiated(self):
        """
        asks to the global orchestrator if the isp graph is instantiated.

        :return: returns true if is yet instantiated somewhere.
        :rtype: bool
        """
        if Session().checkSession(self.isp_id):
            session_id = Session().get_active_user_session(self.isp_id).id
            self.current_domain_id = Graph().get_last_graph(session_id).domain_id

        # TODO substitute this with a controller.get when the get status will be implemented on the UN
        # ask to orchestrator if the isp graph is instantiated
        user_nffg_file = User().getServiceGraph(self.isp_name)
        nffg = NFFG_Manager.getNF_FGFromFile(user_nffg_file)
        user_data = UserData(self.isp_name, self.isp_password, self.isp_tenant)
        orchestrator = GlobalOrchestrator(user_data, self.orchestrator_ip, self.orchestrator_port)
        return UserSession(self.isp_id, None).checkSession(nffg.id, orchestrator)

    @staticmethod
    def _prepare_egress_end_point(nffg, domain_info):
        """
        According to informations exported by the domain about its interfaces, prepare a db
        entry that allow the characterization of the egress end_point

        :param domain_info:
        :type domain_info: DomainInfo
        :return:
        """
        egress_interface_name = None

        if domain_info is not None:
            domain_name = domain_info.name
            for interface in domain_info.interfaces:
                if interface.isEgress():
                    egress_interface_name = interface.name
                    break
        else:
            domain_name = None

        if egress_interface_name is None:
            egress_interface_name = Configuration().EGRESS_PORT

        for end_point in nffg.end_points:
            if end_point.name == Configuration().ISP_EGRESS:
                # prepare an entry for this end point in db
                end_point_db_id = EndPointDB.add_end_point(
                    name=end_point.name,
                    domain=domain_name,
                    _type='interface',
                    interface=egress_interface_name
                )
                # set the database id in the nffg
                end_point.db_id = end_point_db_id

    def get_current_instance(self):
        # get current instance of isp service-graph
        session_id = Session().get_active_user_session(self.isp_id).id
        nffg = NF_FG()
        nffg.parseDict(json.loads(Graph.get_last_graph(session_id).service_graph))
        return nffg
