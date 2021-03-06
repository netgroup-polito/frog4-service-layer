"""
Created on Feb 15, 2015

@author: fabiomignini
"""
import logging, json

from service_layer_application_core.exception import GreIdNotFound, EndPointIdNotFound
from service_layer_application_core.nffg_manager import NFFG_Manager
from service_layer_application_core.config import Configuration
from service_layer_application_core.sql.domains_info import DomainInformation
from service_layer_application_core.sql.end_point import EndPointDB
from service_layer_application_core.sql.node import Node

ISP_INGRESS = Configuration().ISP_INGRESS
ISP_EGRESS = Configuration().ISP_EGRESS
CONTROL_INGRESS = Configuration().CONTROL_INGRESS
USER_INGRESS = Configuration().USER_INGRESS
REMOTE_USER_INGRESS = Configuration().REMOTE_USER_INGRESS
CONTROL_EGRESS = Configuration().CONTROL_EGRESS
CP_CONTROL = Configuration().CP_CONTROL
USER_EGRESS = Configuration().USER_EGRESS

EGRESS_PORT = Configuration().EGRESS_PORT
EGRESS_TYPE = Configuration().EGRESS_TYPE

ISP = Configuration().ISP


class Endpoint(object):
    def __init__(self, nffg):
        self.nffg = nffg

    # not used
    def connectEndpointSwitchToVNFs(self):
        manage = NFFG_Manager(self.nffg)

        for endpoint in self.nffg.end_points:
            if endpoint.name == CONTROL_INGRESS or endpoint.name == ISP_INGRESS:
                manage.connectEndpointSwitchToVNF(endpoint)

    def characterizeEndpoint(self, user_id=None):
        # Characterize INGRESS endpoint
        for endpoint in self.nffg.end_points:
            # Connects directly vnf with endpoint_switch, that means get rid of egress_endpoint           
            if endpoint.name == ISP_EGRESS:
                end_point_model = EndPointDB.get_end_point(endpoint.db_id)
                # if end_point_model is None:
                #     endpoint.type = EGRESS_TYPE
                #     endpoint.interface = EGRESS_PORT
                if end_point_model.domain_name is not None:
                    endpoint.domain = end_point_model.domain_name
                endpoint.type = end_point_model.type
                endpoint.interface = end_point_model.interface

                # if user_id is not None:
                #     endpoint.node = Node().getNodeDomainID(Node().getUserLocation(user_id))
            elif endpoint.name == CONTROL_EGRESS and ISP is False:
                endpoint.type = EGRESS_TYPE
                endpoint.interface = EGRESS_PORT
                # if user_id is not None:
                #     endpoint.node = Node().getNodeDomainID(Node().getUserLocation(user_id))
            # elif endpoint.name == USER_INGRESS:
            #     endpoint.type = INGRESS_TYPE
            #     endpoint.interface = INGRESS_PORT
            #     if user_id is not None:
            #         endpoint.node = Node().getNodeDomainID(Node().getUserLocation(user_id))
            elif endpoint.name == USER_INGRESS or endpoint.name == REMOTE_USER_INGRESS:
                end_point_model = EndPointDB.get_end_point(endpoint.db_id)
                if end_point_model is None:
                    raise EndPointIdNotFound(
                        "The end point '" + endpoint.id + "' have not an entry prepared in the database."
                    )
                endpoint.domain = end_point_model.domain_name
                endpoint.type = end_point_model.type
                endpoint.interface = end_point_model.interface
                # if user_id is not None:
                #     endpoint.node = Node().getNodeDomainID(Node().getUserLocation(user_id))
            elif endpoint.name == CP_CONTROL:
                end_point_model = EndPointDB.get_end_point(endpoint.db_id)
                if end_point_model is None:
                    raise EndPointIdNotFound(
                        "The end point '" + endpoint.id + "' have not an entry prepared in the database."
                    )
                endpoint.domain = end_point_model.domain_name
                endpoint.type = end_point_model.type
                endpoint.interface = end_point_model.interface
            elif endpoint.name == ISP_INGRESS:
                end_point_model = EndPointDB.get_end_point(endpoint.db_id)
                if end_point_model is None:
                    raise EndPointIdNotFound(
                        "The end point '" + endpoint.id + "' have not an entry prepared in the database."
                    )
                endpoint.domain = end_point_model.domain_name
                endpoint.type = end_point_model.type
                if endpoint.type == 'interface':
                    endpoint.interface = end_point_model.interface
                elif endpoint.type == 'internal':
                    endpoint.internal_group = end_point_model.interface
            elif endpoint.name == USER_EGRESS:
                end_point_model = EndPointDB.get_end_point(endpoint.db_id)
                if end_point_model is None:
                    raise EndPointIdNotFound(
                        "The end point '" + endpoint.id + "' have not an entry prepared in the database."
                    )
                endpoint.domain = end_point_model.domain_name
                endpoint.type = end_point_model.type
                if endpoint.type == 'interface':
                    endpoint.interface = end_point_model.interface
                elif endpoint.type == 'internal':
                    endpoint.internal_group = end_point_model.interface
            else:
                endpoint.type = 'internal'
            logging.debug("End-point characterized: " + json.dumps(endpoint.getDict(domain=True)))
