"""
Created on Apr 12, 2016

@author: gabrielecastellano
"""

from doubledecker.clientSafe import ClientSafe
import logging
import json

from service_layer_application_core.config import Configuration
from service_layer_application_core.isp_graph_manager import ISPGraphManager
from .domain_info import DomainInfo
from .sql.domain import Domain
from .sql.domains_info import DomainInformation
from .authentication_graph_manager import AuthGraphManager

BLIND_ISP_DEPLOYMENT = Configuration().BLIND_ISP_DEPLOYMENT

class DDClient(ClientSafe):

    def __init__(self, name, dealer_url, customer, keyfile):
        super().__init__(name, dealer_url, customer, keyfile)
        logging.info("Doubledecker Client State: disconnected")
        self.isp_graph_manager = ISPGraphManager()
        self.auth_graph_manager = AuthGraphManager()

        if BLIND_ISP_DEPLOYMENT:
            # request to instantiate the isp graph on the default domain
            if not self.isp_graph_manager.is_instantiated():
                self.isp_graph_manager.instantiate_isp_graph()
                if self.auth_graph_manager.is_instantiated():
                    self.auth_graph_manager.delete_auth_graph()
            # request to instantiate the authentication graph on the default domain
            if self.isp_graph_manager.is_instantiated() and not self.auth_graph_manager.is_instantiated():
                self.auth_graph_manager.instantiate_auth_graph()
        self.detached_domains = []

    def on_data(self, dst, msg):
        print(dst, " sent", msg)

    def on_discon(self):
        logging.info("Doubledecker Client State: disconnected")

    def on_pub(self, src, topic, msg):
        # new domain information
        msg_str = "PUB %s from %s" % (str(topic), str(src))
        print(msg_str)
        # TODO validate message

        try:
            domain = src.decode("utf-8")
            domain_info = json.loads(msg.decode("utf-8"))

            # domain info
            di = DomainInfo()
            di.parseDict(domain_info)

            domain_id = Domain().add_domain(di.name, di.type)
            di.domain_id = domain_id

            logging.debug("Domain information arrived from %s: %s" % (domain, json.dumps(domain_info)))
            DomainInformation().add_domain_info(di)

            # if the isp and authentication graph are not still in the network, and this is a compatible domain,
            # we try to instantiate them here:
            if not self.isp_graph_manager.is_instantiated():
                self.isp_graph_manager.instantiate_isp_graph(di)
                if self.auth_graph_manager.is_instantiated():
                    self.auth_graph_manager.delete_auth_graph()
            if self.isp_graph_manager.is_instantiated() and not self.auth_graph_manager.is_instantiated():
                self.auth_graph_manager.instantiate_auth_graph(di)

            # add this new domain as end-point in the instantiated authentication graph
            if self.auth_graph_manager.is_instantiated():
                self.auth_graph_manager.add_access_end_points(di)
                while len(self.detached_domains) > 0:
                    self.auth_graph_manager.add_access_end_points(self.detached_domains[0])
                    self.detached_domains.pop(0)
            else:
                self.detached_domains.append(di)
                pass

        except Exception as ex:
            logging.exception(ex)

    # dd ClientSafe call this method without src and msg parameters, so if i override correctly with
    # this parameters (as requested from ClientInterface), there will be an error at any registration
    # and there will be a registration infinite loop.
    # TODO publish an issue on dd repository
    def on_reg(self):
        logging.info("Doubledecker Client State: connected")
        self.subscribe("frog:domain-description", "/0/0/0/")

    def unsubscribe(self, topic, scope):
        pass

    def on_error(self, code, msg):
        pass
