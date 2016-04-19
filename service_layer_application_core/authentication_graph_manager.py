"""
Created on Apr 14, 2016

@author: gabrielecastellano
"""
import json
import logging

from service_layer_application_core.common.user_session import UserSession
from service_layer_application_core.config import Configuration
from service_layer_application_core.controller import ServiceLayerController
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

    def instantiate_auth_graph(self, domain_info=None):
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

    def add_remote_end_points(self, remote_domain_info):
        """
        Add a new remote end-point to the currently instantiated authentication graph,
        and ask for an update of this graph
        :param remote_domain_info: the new domain to attach
        :return:
        :type remote_domain_info: DomainInfo
        """

        # get current instance of authentication service-graph
        session_id = Session().get_active_user_session(self.admin_id).id
        current_domain_name = Domain().get_domain(self.current_domain_id).name
        nffg = NF_FG()
        nffg.parseDict(json.loads(Graph.get_last_graph(session_id).service_graph))
        if nffg is not None:
            if remote_domain_info.name != current_domain_name:

                # get the outer interface of the new domain (maybe I don't need it really)
                new_domain_internet_interface = remote_domain_info.getInternetInterfaceIfAny()
                if new_domain_internet_interface is None:
                    logging.error("New domain does not have an internet interface, it will not be added to auth-graph")
                    return

                logging.debug("Adding end points to auth-graph for the new domain: '" + remote_domain_info.name + "'")

                for interface in remote_domain_info.interfaces:
                    # TODO this check will be 'interface.type == "access"'
                    if len(interface.neighbors) == 0:

                        # prepare a db entry for this end-point to allow the future characterization
                        end_point_db_id = EndPointDB.add_end_point(
                            name=Configuration().REMOTE_USER_INGRESS,
                            domain=remote_domain_info.name,
                            _type='interface',
                            interface=interface.name
                        )
                        # create a new end-point
                        end_point = EndPoint(
                            _id=nffg.getNextAvailableEndPointId(),
                            name=Configuration().REMOTE_USER_INGRESS,
                            db_id=end_point_db_id
                        )
                        nffg.addEndPoint(end_point)
                        logging.debug("Endpoint '" + end_point.id + "' created")

                        # add a new port to the switch VNF
                        switch_vnf = nffg.getVNF("00000001")
                        port_label = switch_vnf.ports[0].id.split(":")[0]
                        new_relative_id = int(switch_vnf.getHigherReletiveIDForPortLabel(port_label)) + 1
                        new_port = Port(port_label + ":" + str(new_relative_id))
                        switch_vnf.addPort(new_port)
                        logging.debug("New port '" + new_port.id + "' inserted into switch VNF")
                        logging.debug("New VNF: '" + str(switch_vnf.getDict()))

                        # insert two flow rules to connect the end point to the switch VNF
                        logging.debug("Creating flow rules for endpoint '" + end_point.id + "'...")
                        to_user_flow_rule = FlowRule(
                            _id=nffg.getNextAvailableFlowRuleId(),
                            priority=1,
                            match=Match(port_in='vnf:'+switch_vnf.id+':'+new_port.id)
                        )
                        to_user_flow_rule.actions.append(Action(output='endpoint:'+end_point.id))
                        nffg.addFlowRule(to_user_flow_rule)
                        logging.debug("Appended flow rule: " + str(to_user_flow_rule.getDict()))
                        from_user_flow_rule = FlowRule(
                            _id=nffg.getNextAvailableFlowRuleId(),
                            priority=1,
                            match=Match(port_in='endpoint:'+end_point.id)
                        )
                        from_user_flow_rule.actions.append(Action(output='vnf:'+switch_vnf.id+':'+new_port.id))
                        nffg.addFlowRule(from_user_flow_rule)
                        logging.debug("Appended flow rule: " + str(from_user_flow_rule.getDict()))
                # update the authentication graph
                self.update(nffg)
            else:
                # TODO this is the domain with the auth-graph! Should we add also its interfaces as end-points?
                pass

    def instantiate_remote_graph(self, remote_domain_name, new_domain_nffg):

        try:
            logging.info("Instantiating the remote graph on the new domain")
            user_data = UserData(self.admin_name, self.admin_password, self.admin_tenant)
            controller = ServiceLayerController(user_data)
            controller.put(domain_name=remote_domain_name, nffg=new_domain_nffg)
            logging.info("Remote graph correctly instantiated on domain '" + remote_domain_name + "'")
            print("Remote graph correctly instantiated")
        except Exception as err:
            logging.error("Failed to instantiate the remote graph.")
            logging.exception(err)
