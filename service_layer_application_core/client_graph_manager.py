"""
Created on Apr 21, 2016

@author: gabrielecastellano
"""

#import json
import logging

from virtualizer_library.virtualizer import ET, Virtualizer,  Software_resource, Infra_node, Port as Virt_Port
#from nffg_library.nffg import EndPoint, FlowRule, Match, Action, NF_FG
from service_layer_application_core.authentication_graph_manager import AuthGraphManager
from service_layer_application_core.common.user_session import UserSession
from service_layer_application_core.config import Configuration
from service_layer_application_core.exception import GraphNotFound, SessionNotFound
#from service_layer_application_core.nffg_manager import NFFG_Manager
from service_layer_application_core.orchestrator_rest import GlobalOrchestrator
#from service_layer_application_core.sql.end_point import EndPointDB
#from service_layer_application_core.sql.graph import Graph
from service_layer_application_core.sql.session import Session
from service_layer_application_core.sql.user import User
from service_layer_application_core.user_authentication import UserData

ISP_INGRESS = Configuration().ISP_INGRESS
USER_EGRESS = Configuration().USER_EGRESS


class ClientGraphManager:

    orchestrator_ip = Configuration().ORCH_IP
    orchestrator_port = Configuration().ORCH_PORT

    def __init__(self, user_data, delete=None):
        """

        :param user_data:
        :type user_data: UserData
        """
        self.user_name = user_data.username
        self.user_password = user_data.password
        self.user_tenant = user_data.tenant
        self.user_id = User().getUser(self.user_name).id
        self.current_domain_id = None
        self.delete = delete
        #get the user service graph instance from db
        #self.nffg = self._get_current_instance()
        #if self.nffg is None:
        #TODO extend the support to multiple device per user-->for now one user and one device per time
        self.nffg = self._get_user_defined_graph()
        logging.debug("loaded template user graph from file")

    def add_endpoint_from_auth_switch_interface(self, vnf_interface_name):
        """
        add a new ingress end_point to the graph and prepare an entry in the db
        :param vnf_interface_name:
        :return:
        """

        # get the user end point from current authentication graph
        auth_graph_manger = AuthGraphManager()
        auth_user_end_point = auth_graph_manger.get_endpoint_from_switch_port(vnf_interface_name)
        # declaration of the new endpoint
        service_user_end_point = EndPoint()

        # check if this interface have yet an endpoint in the user graph
        end_point_is_present = False
        for old_end_point in self.nffg.end_points:
            if old_end_point.db_id == auth_user_end_point.db_id:
                end_point_is_present = True
                service_user_end_point.id = old_end_point.id
                service_user_end_point.name = old_end_point.name
                service_user_end_point.db_id = old_end_point.db_id
                break

        if not end_point_is_present:
            # create a new end_point for this user
            service_user_end_point = EndPoint(
                _id=self.nffg.getNextAvailableEndPointId(),
                name=auth_user_end_point.name,
                db_id=auth_user_end_point.db_id
            )
            self.nffg.addEndPoint(service_user_end_point)
            logging.debug("Endpoint '" + service_user_end_point.id + "' created: " +
                          json.dumps(service_user_end_point.getDict(extended=True, domain=True)))

            # get the user ingress port
            ingress_vnf, user_port = self._get_user_ingress_port()
            logging.debug("User port is: '" + user_port.id + "' of vnf: '" + ingress_vnf.id + "'")

            # insert two flow rules to connect the end point to the first VNF
            logging.debug("Creating flow rules for endpoint '" + service_user_end_point.id + "'...")
            to_user_flow_rule = FlowRule(
                _id=self.nffg.getNextAvailableFlowRuleId(),
                priority=10,
                match=Match(port_in='vnf:' + ingress_vnf.id + ':' + user_port.id)
            )
            to_user_flow_rule.actions.append(Action(output='endpoint:' + service_user_end_point.id))
            self.nffg.addFlowRule(to_user_flow_rule)
            logging.debug("Appended flow rule: " + str(to_user_flow_rule.getDict()))
            from_user_flow_rule = FlowRule(
                _id=self.nffg.getNextAvailableFlowRuleId(),
                priority=10,
                match=Match(port_in='endpoint:' + service_user_end_point.id)
            )
            from_user_flow_rule.actions.append(Action(output='vnf:' + ingress_vnf.id + ':' + user_port.id))
            self.nffg.addFlowRule(from_user_flow_rule)
            logging.debug("Appended flow rule: " + str(from_user_flow_rule.getDict()))
        else:
            # the end point is present, so the controller will simply add the flow rules for this device
            logging.debug("There is yet an end point for this interface in the user graph.")

        return service_user_end_point.id

    def delete_endpoint_from_user_device_if_last(self, mac_address):

        user_device = Session().get_user_device(self.user_id, mac_address)
        user_devices = Session().get_active_user_devices_for_endpoint(self.user_id, user_device.endpoint_id)

        # delete endpoint if is the last device
        if len(user_devices) == 1:
            # delete flow rules
            to_user_flow_rules = self.nffg.getFlowRulesSendingTrafficToEndPoint(user_device.endpoint_id)
            for flow_rule in to_user_flow_rules:
                self.nffg.flow_rules.remove(flow_rule)
            from_user_flow_rules = self.nffg.getFlowRulesSendingTrafficFromEndPoint(user_device.endpoint_id)
            for flow_rule in from_user_flow_rules:
                self.nffg.flow_rules.remove(flow_rule)
            # delete endpoint
            self.nffg.end_points.remove(self.nffg.getEndPoint(user_device.endpoint_id))

    def prepare_egress_end_point(self):
        """
        prepare the egress end_point of the client graph to connect it with isp
        :return:
        """
        from service_layer_application_core.isp_graph_manager import ISPGraphManager

        user_egress_endpoint = self.nffg.getEndPointsFromName(USER_EGRESS)[0]
        if user_egress_endpoint is not None:
            isp_graph_manager = ISPGraphManager()
            isp_nffg = isp_graph_manager.get_current_instance()
            isp_end_point_model = EndPointDB.get_end_point(
                isp_nffg.getEndPointsFromName(ISP_INGRESS)[0].db_id
            )
            # prepare an entry for this end point in db
            user_egress_endpoint_db_id = EndPointDB.add_end_point(
                name=user_egress_endpoint.name,
                domain=isp_end_point_model.domain_name,
                _type='internal',
                interface=isp_end_point_model.interface
            )
            # set the database id in the nffg
            user_egress_endpoint.db_id = user_egress_endpoint_db_id

    def is_instantiated(self):
        """
        asks to the global orchestrator if the graph for this user is instantiated.

        :return: returns true if is yet instantiated somewhere.
        :rtype: bool
        """
        if Session().checkSession(self.user_id):
            session_id = Session().get_active_user_session(self.user_id).id
            self.current_domain_id = Graph().get_last_graph(session_id).domain_id

        # TODO substitute this with a controller.get when the get status will be implemented on the UN
        # ask to orchestrator if the authentication graph is instantiated
        user_nffg_file = User().getServiceGraph(self.user_name)
        nffg = NFFG_Manager.getNF_FGFromFile(user_nffg_file)
        user_data = UserData(self.user_name, self.user_password, self.user_tenant)
        orchestrator = GlobalOrchestrator(user_data, self.orchestrator_ip, self.orchestrator_port)
        return UserSession(self.user_id, None).checkSession(nffg.id, orchestrator)

    def _get_current_instance(self):
        """

        :return:
        :rtype: NF_FG
        """
        try:
            session_id = Session().get_active_user_session(self.user_id).id
            # current_domain_name = Domain().get_domain(self.current_domain_id).name
            nffg = NF_FG()
            nffg.parseDict(json.loads(Graph.get_last_graph(session_id).service_graph))
        except SessionNotFound:
            nffg = None
        return nffg

    def _get_user_defined_graph(self):
        """

        :return:
        :rtype: NF_FG
        """
        # if it is the first device for this user, we get it from the file
        nffg_file = User().getServiceGraph(self.user_name)
        if nffg_file is None:
            raise GraphNotFound("No graph defined for the user '" + self.user_name + "'")
        if self.delete == True:
            logging.debug("Graph delete_%s find for the user %s", nffg_file, self.user_name)
            try:
                tmpFile = open("graphs/delete_" + nffg_file, "r")
                escapeNffg = tmpFile.read()
                tmpFile.close()
            except IOError as e:
                print("Failed to read " + nffg_file)
                logging.error("Failed to read " + nffg_file)
                logging.exception(e)
            return escapeNffg
        else:
            logging.debug("Graph %s find for the user %s", nffg_file, self.user_name)
            try:
                tmpFile = open("graphs/" + nffg_file, "r")
                escapeNffg = tmpFile.read()
                tmpFile.close()
            except IOError as e:
                print("Failed to read " + nffg_file)
                logging.error("Failed to read " + nffg_file)
                logging.exception(e)
            return escapeNffg

    def _get_user_ingress_port(self):
        for vnf in self.nffg.vnfs:
            for port in vnf.ports:
                if port.name == 'user':
                    return vnf, port
