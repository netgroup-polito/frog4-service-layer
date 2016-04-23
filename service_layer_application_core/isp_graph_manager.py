"""
Created on Apr 21, 2016

@author: gabrielecastellano
"""

import json
import logging

from nffg_library.nffg import EndPoint, Port, FlowRule, Match, Action
from service_layer_application_core.authentication_graph_manager import AuthGraphManager
from service_layer_application_core.exception import GraphNotFound
from service_layer_application_core.nffg_manager import NFFG_Manager
from service_layer_application_core.sql.user import User


class ClientGraphManager:

    def __init__(self, user_data):
        """

        :param user_data:
        :type user_data: UserData
        """
        self.user_data = user_data
        # get the user service graph from db
        nffg_file = User().getServiceGraph(user_data.username)
        if nffg_file is None:
            raise GraphNotFound("No graph defined for the user '" + user_data.username + "'")
        self.nffg = NFFG_Manager.getNF_FGFromFile(nffg_file)

    def add_end_point_from_auth_switch_interface(self, vnf_interface_name):
        """
        add a new ingress end_point to the graph and prepare an entry in the db
        :param vnf_interface_name:
        :return:
        """

        # get the user end point from current authentication graph
        auth_graph_manger = AuthGraphManager()
        auth_user_end_point = auth_graph_manger.get_end_point_from_switch_port(vnf_interface_name)

        # create a new end_point for this user
        service_user_end_point = EndPoint(
            _id=self.nffg.getNextAvailableEndPointId(),
            name=auth_user_end_point.name,
            db_id=auth_user_end_point.db_id
        )
        self.nffg.addEndPoint(service_user_end_point)
        logging.debug("Endpoint '" + service_user_end_point.id + "' created: " +
                      json.dumps(service_user_end_point.getDict(extended=True, domain=True)))

        # add a new port to the switch VNF
        switch_vnf = self.nffg.getVNF("00000001")
        port_label = switch_vnf.ports[0].id.split(":")[0]
        new_relative_id = int(switch_vnf.getHigherReletiveIDForPortLabel(port_label)) + 1
        new_port = Port(port_label + ":" + str(new_relative_id))
        switch_vnf.addPort(new_port)
        logging.debug("New port '" + new_port.id + "' inserted into switch VNF")
        logging.debug("Updated VNF: '" + str(switch_vnf.getDict(domain=True)))

        # insert two flow rules to connect the end point to the switch VNF
        logging.debug("Creating flow rules for endpoint '" + service_user_end_point.id + "'...")
        to_user_flow_rule = FlowRule(
            _id=self.nffg.getNextAvailableFlowRuleId(),
            priority=10,
            match=Match(port_in='vnf:' + switch_vnf.id + ':' + new_port.id)
        )
        to_user_flow_rule.actions.append(Action(output='endpoint:' + service_user_end_point.id))
        self.nffg.addFlowRule(to_user_flow_rule)
        logging.debug("Appended flow rule: " + str(to_user_flow_rule.getDict()))
        from_user_flow_rule = FlowRule(
            _id=self.nffg.getNextAvailableFlowRuleId(),
            priority=1,
            match=Match(port_in='endpoint:' + service_user_end_point.id)
        )
        from_user_flow_rule.actions.append(Action(output='vnf:' + switch_vnf.id + ':' + new_port.id))
        self.nffg.addFlowRule(from_user_flow_rule)
        logging.debug("Appended flow rule: " + str(from_user_flow_rule.getDict()))

    def prepare_egress_end_point(self):
        """
        prepare the egress end_point of the client graph to connect it with isp
        :return:
        """
        # maybe this is yet done by the controller 'remoteConnection' method
        pass




