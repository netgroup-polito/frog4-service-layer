"""
@author: fabiomignini
@author: gabrielecastellano
"""

from __future__ import division

import json
import falcon
import logging
import uuid

from service_layer_application_core.config import Configuration
from service_layer_application_core.sql.domain import Domain
from service_layer_application_core.sql.end_point import EndPointDB
from service_layer_application_core.sql.graph import Graph
from service_layer_application_core.sql.session import Session, UserDeviceModel
from service_layer_application_core.sql.user import User
from nffg_library.nffg import NF_FG
from service_layer_application_core.nffg_manager import NFFG_Manager
from service_layer_application_core.common.user_session import UserSession
from service_layer_application_core.common.endpoint import Endpoint
from service_layer_application_core.orchestrator_rest import GlobalOrchestrator
from service_layer_application_core.exception import SessionNotFound, ISPNotDeployed, GraphNotFound

ISP = Configuration().ISP
ISP_USERNAME = Configuration().ISP_USERNAME
ISP_PASSWORD = Configuration().ISP_PASSWORD
ISP_TENANT = Configuration().ISP_TENANT
# End-points type
USER_EGRESS = Configuration().USER_EGRESS
CONTROL_EGRESS = Configuration().CONTROL_EGRESS
ISP_INGRESS = Configuration().ISP_INGRESS
ISP_EGRESS = Configuration().ISP_EGRESS
CONTROL_INGRESS = Configuration().CONTROL_INGRESS

USER_INGRESS = Configuration().USER_INGRESS

ENRICH_USER_GRAPH = Configuration().ENRICH_USER_GRAPH

DEBUG_MODE = Configuration().DEBUG_MODE

VNF_AWARE_DOMAINS = Configuration().VNF_AWARE_DOMAINS


class ServiceLayerController:

    orchestrator_ip = Configuration().ORCH_IP
    orchestrator_port = Configuration().ORCH_PORT

    def __init__(self, user_data):
        self.user_data = user_data
        self.orchestrator = GlobalOrchestrator(self.user_data, self.orchestrator_ip, self.orchestrator_port)

    def get(self):

        session = Session().get_active_user_session(self.user_data.getUserID())
        logging.debug("Graph id: " + session.service_graph_id)

        status = json.loads(self.orchestrator.getNFFGStatus(session.service_graph_id))
        logging.debug("Response from orchestrator: " + str(status))
        logging.debug("Status : "+status['status'])
        if status['status'] == "complete":
            code = falcon.HTTP_201
        else:
            code = falcon.HTTP_202

        logging.debug("Username : "+self.user_data.username+", Resources : "+json.dumps(status))
        logging.debug("GET from username: "+self.user_data.username+" completed")

        return json.dumps(status), code

    def get_nffg(self):

        session = Session().get_active_user_session(self.user_data.getUserID())
        logging.debug("Graph id: " + session.service_graph_id)

        nffg = self.orchestrator.getNFFG(session.service_graph_id)
        logging.debug("Got graph '" + session.service_graph_id + "' from orchestrator.")

        return nffg

    def delete(self, mac_address, nffg):
        """
        If there are more active session for specific user a delete become an update
        that erase a mac rule of user, otherwise if there is only one active session for the user
        the nf-fg will be de-instantiated

        :param mac_address: the mac which rule has to be erased, if no one is specified,
                            the whole NF_FG will be de-instantiated.
        :param nffg: current instance of nffg for this user
        :type nffg: NF_FG
        """

        # Returns the number of active session for the user, and if exists the session for the requested device
        num_devices, session = Session().get_active_user_device_session(self.user_data.getUserID(),
                                                                        mac_address,
                                                                        error_aware=False)

        if mac_address is not None:
            logging.debug("Delete access for device: "+str(mac_address)+" of User: "+self.user_data.username)
        else:
            logging.debug("Delete user service graph: "+self.user_data.username)
        logging.debug("Number of devices for the user: "+str(num_devices))
        ended = None
        if num_devices == 1:
            # De-instantiate User Profile Graph
            if DEBUG_MODE is False:
                try:
                    self.orchestrator.delete(session.service_graph_id)
                    Graph().delete_session(session.id)
                    Session().delete_user_devices_for_session(session.id)
                    Session().updateStatus(session.id, 'deleted')
                    Session().set_ended(session.id)
                except Exception as err:
                    Session().set_error(session.id)
                    raise err
            else:
                # debug mode
                Graph().delete_session(session.id)
                Session().delete_user_devices_for_session(session.id)

            logging.debug('Deleted profile of user "'+self.user_data.username+'"')
            print('Deleted profile of user "' + self.user_data.username + '"')

            # Set the field ended in the table session to the actual data time
            Session().set_ended(session.id)
        else:
            logging.debug('Delete access for specific device')

            # This delete is an update of the user service graph
            # clone the nffg into a service_graph before to start lowering, so we can add it into db if success
            sl_nffg = NF_FG()
            sl_nffg.parseDict(nffg.getDict(extended=True, domain=True))

            # delete this device
            Session().delete_user_device_for_session(session.id, mac_address=mac_address)

            # add old devices
            self.addDeviceToNF_FG(None, None, nffg)

            logging.debug('New user profile :'+nffg.getJSON(domain=True))

            # Call orchestrator to update NF-FG
            logging.debug('Call orchestrator sending the following NF-FG: '+nffg.getJSON(domain=True))
            if DEBUG_MODE is False:
                try:
                    self.orchestrator.put(nffg)
                    Session().updateStatus(session.id, 'updated')
                    Graph.set_service_graph(Graph.get_last_graph(session.id).id, sl_nffg)
                except Exception as err:
                    Session().set_error(session.id)
                    raise err
            else:
                # debug mode
                Session().updateStatus(session.id, 'updated')
                Graph.set_service_graph(Graph.get_last_graph(session.id).id, sl_nffg)

            logging.debug('Device deleted "'+mac_address+'" of user "'+self.user_data.username+'"')
            print('Device deleted "' + mac_address + '" of user "' + self.user_data.username + '"')

    def put(self, mac_address=None, device_endpoint_id=None, domain_name=None, nffg=None):
        """

        :param mac_address:
        :param device_endpoint_id: the id of the end point in the nffg to which the device is attached
        :param domain_name:
        :param nffg:
        :type mac_address: str
        :type device_endpoint_id: str
        :type domain_name: str
        :type nffg: NF_FG
        :return:
        """

        # Get user network function forwarding graph
        if nffg is None:
            nffg_file = User().getServiceGraph(self.user_data.username)
            if nffg_file is None:
                raise GraphNotFound("No graph defined for the user '" + self.user_data.username + "'")
            nffg = NFFG_Manager.getNF_FGFromFile(nffg_file)

        # if domain is specified, label the nffg with it
        if domain_name is not None:
            nffg.domain = domain_name

        # Check if the user have an active session
        if UserSession(self.user_data.getUserID(), self.user_data).checkSession(nffg.id, self.orchestrator) is True:
            # Existent session for this user
            logging.debug('The FG for this user is already instantiated, the FG will be updated if it has been modified')

            session = Session().get_active_user_session_by_nf_fg_id(nffg.id, error_aware=True)
            session_id = session.id
            Session().updateStatus(session_id, 'updating')

            # clone the nffg into a service_graph before to start lowering, so we can add it into db if success
            sl_nffg = NF_FG()
            sl_nffg.parseDict(nffg.getDict(extended=True, domain=True))

            # Manage new device
            if Session().checkDeviceSession(self.user_data.getUserID(), mac_address) is True:
                '''
                 A rule for this mac address is already implemented,
                 only an update of the graph is needed
                 (This update is necessary only if the graph is different from the last instantiated,
                 but in this moment the graph is always re-instantiated, will be the orchestrator accountable
                 for a smart update of the FG).
                '''
                mac_address = None

            self.addDeviceToNF_FG(mac_address, device_endpoint_id, nffg)

            # Call orchestrator to update NF-FG
            logging.debug('Call orchestrator sending the following NF-FG: '+nffg.getJSON(domain=True))
            if DEBUG_MODE is False:
                try:
                    self.orchestrator.put(nffg)
                    Graph.set_service_graph(Graph.get_last_graph(session_id).id, sl_nffg)
                except Exception as err:
                    Session().set_error(session_id)
                    raise err
            else:
                # debug mode
                Graph.set_service_graph(Graph.get_last_graph(session_id).id, sl_nffg)
            if mac_address is not None:
                logging.info("Added device '"+mac_address+"' of user '"+self.user_data.username+"'")
                print("Added device '"+mac_address+"' of user '"+self.user_data.username+"'")
            else:
                logging.info("User profile updated '"+self.user_data.username+"'")
                print("User profile updated '"+self.user_data.username+"'")
        else:
            # New session for this user
            logging.debug('The FG for this user is not yet instantiated')
            logging.debug('Instantiate profile')
            session_id = uuid.uuid4().hex
            Session().inizializeSession(session_id, self.user_data.getUserID(), nffg.id, nffg.name)

            # set the domain in root if available in endpoint
            if device_endpoint_id is not None and domain_name is None:
                logging.info("Detecting the right domain for the user graph")
                logging.debug("device_endpoint_id: " + device_endpoint_id)
                ep_domain_name = EndPointDB.get_end_point(nffg.getEndPoint(device_endpoint_id).db_id).domain_name
                logging.debug("domain_name " + ep_domain_name)
                domain_type = Domain.get_domain_from_name(ep_domain_name).type
                logging.debug("domain_type " + domain_type)
                if ep_domain_name is not None and domain_type in VNF_AWARE_DOMAINS:
                    nffg.domain = EndPointDB.get_end_point(nffg.getEndPoint(device_endpoint_id).db_id).domain_name

            # clone the nffg into a service_graph before to start lowering, so we can add it into db if success
            sl_nffg = NF_FG()
            sl_nffg.parseDict(nffg.getDict(extended=True, domain=True))

            # Manage profile
            logging.debug("User service graph: "+nffg.getJSON(domain=True))
            self.prepareProfile(mac_address, device_endpoint_id, nffg)

            # Call orchestrator to instantiate NF-FG
            logging.debug('Calling orchestrator sending NF-FG: '+nffg.getJSON(domain=True))
            print("Calling orchestrator to instantiate '"+self.user_data.username+"' forwarding graph.")
            if DEBUG_MODE is False:
                try:
                    self.orchestrator.put(nffg)
                    # add the service graph to db
                    graph_db_id = Graph().add_graph(sl_nffg, session_id)
                    if domain_name is not None:
                        Graph.set_domain_id(graph_db_id, Domain.get_domain_from_name(domain_name).id)
                    logging.debug("Profile instantiated for user '"+self.user_data.username+"'")
                    print("Profile instantiated for user '"+self.user_data.username+"'")
                except Exception as err:
                    logging.exception(err)
                    Session().set_error(session_id)
                    Graph.delete_graph(session_id)
                    logging.debug("Failed to instantiated profile for user '"+self.user_data.username+"'")
                    print("Failed to instantiated profile for user '"+self.user_data.username+"'")
                    raise err
            else:
                # debug mode
                graph_db_id = Graph().add_graph(sl_nffg, session_id)
                if domain_name is not None:
                    Graph.set_domain_id(graph_db_id, Domain.get_domain_from_name(domain_name).id)
                logging.debug("Profile instantiated for user '"+self.user_data.username+"'")
                print("Profile instantiated for user '"+self.user_data.username+"'")

        # Set mac address in the session
        if mac_address is not None:
            Session().add_device_in_the_session(
                mac_address,
                device_endpoint_id,
                nffg.getEndPoint(device_endpoint_id).db_id,
                session_id
            )
        Session().updateStatus(session_id, 'complete')

    def addDeviceToNF_FG(self, mac_address, device_endpoint_id, nffg):
        # Get MAC addresses from previous session
        logging.debug('Get MAC addresses from previous session')
        session_devices = Session().get_active_user_devices(self.user_data.getUserID())
        user_devices = []
        if session_devices is not None:
            user_devices = user_devices + session_devices
        if mac_address is not None:
            logging.debug('new MAC: '+str(mac_address))
            user_devices.append(UserDeviceModel(
                mac_address=mac_address,
                endpoint_id=device_endpoint_id,
                endpoint_db_id=nffg.getEndPoint(device_endpoint_id).db_id
            ))
        logging.debug('User devices: '+str(user_devices))

        # TODO I think that this fabio's check is wronged so I pass always 'False' for now
        # If the graph is already attached to ISP, we don't have to reconnect it again
        if ISP is True and (nffg.getEndPointsFromName(USER_EGRESS) or nffg.getEndPointsFromName(CONTROL_EGRESS)):
            already_connected = True
        else:
            already_connected = False

        self._prepareProfile(nffg, already_connected=False)

        # add ingress flows for all devices (old and news)
        if len(user_devices) != 0:
            manager = NFFG_Manager(nffg)
            manager.addDevicesFlows(user_devices)

    def _prepareProfile(self, nffg, already_connected=False):
        """
        This method performs the following modification to the graph passed as argument:
         if it is an user graph, ingress and egress graph are attached;
         a control connection is added to all VNFs that need it;
         the graph is attached to the ISP;
         useless VNFs are merged;
         each endpoint is characterized, so the type and relative details are added.

        :param nffg: the graph to prepare
        :param already_connected:
        :return:
        """

        manager = NFFG_Manager(nffg)

        if ENRICH_USER_GRAPH and nffg.name != 'Authentication-Graph' and nffg.name != 'ISP-Graph':
            # Get INGRESS NF-FG
            logging.debug('Getting INGRESS NF-FG')
            ingress_nf_fg = manager.getIngressNF_FG()

            # Attach INGRESS NF_FG to USER_INGRESS ENDPOINT
            logging.debug('Attach INGRESS NF_FG to USER_INGRESS ENDPOINT')
            # logging.info(ingress_nf_fg.getJSON())
            manager.attachIngressNF_FG(ingress_nf_fg)

            # Get EGRESS NF-FG
            logging.debug('Getting EGRESS NF-FG')
            egress_nf_fg = manager.getEgressNF_FG()

            # Attach EGRESS NF_FG to USER_EGRESS ENDPOINT
            logging.debug('Attach EGRESS NF_FG to USER_EGRESS ENDPOINT')
            manager.attachEgressNF_FG(egress_nf_fg)

        # Add control network
        logging.debug('Adding control network')
        for vnf in nffg.vnfs:
            logging.debug('Getting template for vnf: ' + vnf.name + ' (file ' + vnf.vnf_template_location + ')')
            template = self.orchestrator.getTemplate(vnf.vnf_template_location)
            need_control_net, port = manager.checkIfControlNetIsNedeed(vnf, template)
            if need_control_net is True:
                if ISP is True and nffg.name != 'ISP_graph':
                    control_switch = manager.addPortToControlNet(vnf, port.id, CONTROL_EGRESS)
                else:
                    control_switch = manager.addPortToControlNet(vnf, port.id, ISP_EGRESS)

                if nffg.name == 'ISP_graph':
                    user_control_egress = manager.createEndPoint(CONTROL_INGRESS)
                    port = manager.createSwitchPort(control_switch)
                    control_switch.ports.append(port)
                    manager.connectVNFAndEndPoint(vnf_id=control_switch.id, port_id=port.id, end_point_id=user_control_egress.id)

        # TODO: if end-point is ... then connect to ISP
        # Create connection to another NF-FG
        # TODO: The following row should be executed only if we want to concatenate ISP to our graphs
        # if ISP is True and nffg.name != 'ISP-Graph' and not already_connected:
        #    self.remoteConnection(nffg)

        manager.mergeUselessVNFs()

        Endpoint(nffg).characterizeEndpoint(User().getUser(self.user_data.username).id)

    def prepareProfile(self, mac_address, device_endpoint_id, nffg):
        """
        This function transform the Service Graph passed to a Forwarding Graph.
        In addiction adds the flow rule for the user device.

        :param mac_address: if specified, an ingress flow rule for this device will be added to the nffg
        :param device_endpoint_id:
        :param nffg: the graph to prepare
        :return:
        """
        # Transform profile in NF_FG
        manager = NFFG_Manager(nffg)

        self._prepareProfile(nffg)

        # Add flow that permits to user device to reach his NF-FG  
        if mac_address is not None:
            logging.debug('Adding device flows for mac address: ' + str(mac_address))
            user_device = UserDeviceModel(
                mac_address=mac_address,
                endpoint_id=device_endpoint_id,
                endpoint_db_id=nffg.getEndPoint(device_endpoint_id).db_id
            )
            manager.setDeviceFlows(user_device)
        else:
            logging.warning("No mac address specified for this request (user '" + self.user_data.username + "')")

    def remoteConnection(self, nffg):
        """
        Connect the nf_fg passed with the ISP graph
        """
        # isp_user_data = UserData(usr=ISP_USERNAME, pwd=ISP_PASSWORD, tnt=ISP_TENANT)

        try:
            from service_layer_application_core.isp_graph_manager import ISPGraphManager
            isp_graph_manager = ISPGraphManager()
            control_egress_endpoint = nffg.getEndPointsFromName(CONTROL_EGRESS)
            if control_egress_endpoint:
                # remote_endpoint_id = self.orchestrator.getNFFG(Session().get_profile_id_from_active_user_session(isp_user_data.getUserID()))\
                #                             .getEndPointsFromName(CONTROL_INGRESS)[0].id
                # control_egress_endpoint[0].remote_endpoint_id = Session().get_profile_id_from_active_user_session(isp_user_data.getUserID())\
                #     +':'+remote_endpoint_id
                isp_nffg = isp_graph_manager.get_current_instance()
                remote_endpoint_id = isp_nffg.getEndPointsFromName(CONTROL_INGRESS)[0].id
                control_egress_endpoint[0].remote_endpoint_id = isp_nffg.id + ':' + remote_endpoint_id
            user_egress_endpoint = nffg.getEndPointsFromName(USER_EGRESS)
            if user_egress_endpoint:
                # remote_endpoint_id = self.orchestrator.getNFFG(Session().get_profile_id_from_active_user_session(isp_user_data.getUserID()))\
                #                             .getEndPointsFromName(ISP_INGRESS)[0].id
                # user_egress_endpoint[0].remote_endpoint_id = Session().get_profile_id_from_active_user_session(isp_user_data.getUserID())\
                #     +':'+remote_endpoint_id
                isp_nffg = isp_graph_manager.get_current_instance()
                remote_endpoint_id = isp_nffg.getEndPointsFromName(ISP_INGRESS)[0].id
                user_egress_endpoint[0].remote_endpoint_id = isp_nffg.id + ':' + remote_endpoint_id
                user_egress_endpoint[0].domain = Domain.get_domain(isp_graph_manager.current_domain_id).name
        except SessionNotFound:
            raise ISPNotDeployed("ISP's graph not deployed. By config the SL try to connect the user service graph to the ISP's graph.")
        except Exception:
            raise ISPNotDeployed("ISP's graph not deployed. By config the SL try to connect the user service graph to the ISP's graph.")

    def deleteRemoteConnections(self):
        raise NotImplementedError()
