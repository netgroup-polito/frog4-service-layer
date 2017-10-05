"""
@author: fabiomignini
@author: gabrielecastellano
@author_jolnet_version: Francesco Lubrano
"""

from __future__ import division

import falcon
import logging
import uuid
import xml.etree.ElementTree as ET

from service_layer_application_core.config import Configuration

from service_layer_application_core.sql.graph import Graph
from service_layer_application_core.sql.session import Session, UserDeviceModel
from service_layer_application_core.sql.user import User
from service_layer_application_core.common.user_session import UserSession
from service_layer_application_core.orchestrator_rest import GlobalOrchestrator
from service_layer_application_core.exception import SessionNotFound, GraphNotFound

from virtualizer_library.virtualizer import Virtualizer,  Software_resource, Infra_node, Port as Virt_Port

DEBUG_MODE = Configuration().DEBUG_MODE



class ServiceLayerController:

    orchestrator_ip = Configuration().ORCH_IP
    orchestrator_port = Configuration().ORCH_PORT

    def __init__(self, user_data):
        self.user_data = user_data
        self.orchestrator = GlobalOrchestrator(self.orchestrator_ip, self.orchestrator_port)

    def get_nffg(self):

        nffg = self.orchestrator.getNFFG()
        logging.debug("Got graph from orchestrator.")
        return nffg

    def delete(self, nffg, mac_address=None):
        """
        :param mac_address: the mac which rule has to be erased, if no one is specified,
                            the whole NF_FG will be de-instantiated.
        :param nffg: current instance of nffg for this user
        :type nffg: NF_FG
        """

        logging.debug("Delete user service graph: "+self.user_data.username)
        if nffg is not None:
            # Graph parsing
            try:
                tree = ET.ElementTree(ET.fromstring(nffg))
                root = tree.getroot()
            except ET.ParseError as e:
                print('ParseError: %s' % e.message)
                logging.exception(e)
                Session().set_error(session_id)
                raise e 
            newInfrastructure = Virtualizer.parse(root=root)
            newFlowtable = newInfrastructure.nodes.node['SingleBiSBiS'].flowtable
            newNfInstances = newInfrastructure.nodes.node['SingleBiSBiS'].NF_instances
            # Call orchestrator to get the actual configuration
            logging.debug('Calling orchestrator getting actual configuration')
            try:
                mdo_config = self.orchestrator.getNFFG()
                logging.debug('Retrieved configuration: ')
                logging.debug(mdo_config)
            except Exception as err:
                logging.exception(err)
                Session().set_error(session_id)
                logging.debug("Failed to retrieve MdO configuration ")
                raise err
            try:
                original_tree = ET.ElementTree(ET.fromstring(mdo_config))
                original_root = original_tree.getroot()
            except Exception as err:
                logging.exception(err)
                Session().set_error(session_id)
                logging.debug("Failed to retrieve MdO configuration ")
                raise err
            Infrastructure = Virtualizer.parse(root=original_root)
            Flowtable = Infrastructure.nodes.node['SingleBiSBiS'].flowtable
            NfInstances = Infrastructure.nodes.node['SingleBiSBiS'].NF_instances

            for instance in newNfInstances:
                todelete_id = instance.id.get_value()
                for mdo_instance in NfInstances:
                    if mdo_instance.id.get_value() == todelete_id:
                        mdo_instance.set_operation('delete', recursive=False)
            for flowentry in newFlowtable:
                flowtodelete_id = flowentry.id.get_value()
                for mdo_flowentry in Flowtable:
                    if mdo_flowentry.id.get_value() == flowtodelete_id:
                        mdo_flowentry.set_operation('delete', recursive=False)

            # Adding the user graph to the original configuration
            nffg = Infrastructure.xml()
        # De-instantiate User Profile Graph
        if DEBUG_MODE is False:
            try:
                self.orchestrator.put(nffg)
                logging.debug("Profile deleted for user '"+self.user_data.username+"'")
                print("Profile deleted for user '"+self.user_data.username+"'")
            except Exception as err:
                logging.exception(err)
                Session().set_error(session_id)
                logging.debug("Failed to instantiated profile for user '"+self.user_data.username+"'")
                print("Failed to instantiated profile for user '"+self.user_data.username+"'")
                raise err
        else:
            # debug mode
            #graph_db_id = Graph().add_graph(sl_nffg, session_id)
            #if domain_name is not None:
            #    Graph.set_domain_id(graph_db_id, Domain.get_domain_from_name(domain_name).id)
            logging.debug(nffg)
        logging.debug('Deleted profile of user "'+self.user_data.username+'"')
        print('Deleted profile of user "' + self.user_data.username + '"')

        # Set the field ended in the table session to the actual data time
        #TODO scommentare la riga sotto alla fine del debug
        #Session().set_ended(session.id)
 
    def put(self, mac_address=None, location=None, is_user=False, domain_name=None, nffg=None):
        """

        :param mac_address:
        :param device_endpoint_id: the id of the end point in the nffg to which the device is attached
        :param domain_name:
        :param location: str
        :param nffg:
        :type mac_address: str
        :type device_endpoint_id: str
        :type domain_name: str
        :type nffg: escapeNffg
        :return:
        """

        # Get user network function forwarding graph
        if nffg is None:
            nffg_file = User().getServiceGraph(self.user_data.username) #get file from db
            if nffg_file is None:
                raise GraphNotFound("No graph defined for the user '" + self.user_data.username + "'")
            nffg = NFFG_Manager.getNF_FGFromFile(nffg_file)

        # if domain is specified, label the nffg with it
        if domain_name is not None:
            nffg.domain = domain_name
        # Check if the user have an active session TODO: aggiungere check con get_active_user_session
        #if UserSession(self.user_data.getUserID(), self.user_data).checkSession(nffg.id, self.orchestrator) is True:
        if is_user is True:
            # User graph
            logging.debug('The FG for this user with this device is not yet instantiated')
            logging.debug('Instantiate profile')
            session_id = uuid.uuid4().hex
            graph_name = ''
            if nffg is not None:
                # Graph parsing
                flag = True
                logging.debug("+++++++++++++++++++++++++++++++++++++++++")
                nffg = addFlows(self, nffg, location)

                try:
                    tree = ET.ElementTree(ET.fromstring(nffg))
                    root = tree.getroot()
                except ET.ParseError as e:
                    print('ParseError: %s' % e.message)
                    raise ServerError("ParseError: %s" % e.message)
                newInfrastructure = Virtualizer.parse(root=root)
                newFlowtable = newInfrastructure.nodes.node['SingleBiSBiS'].flowtable
                newNfInstances = newInfrastructure.nodes.node['SingleBiSBiS'].NF_instances
                for child in newNfInstances:
                    graph_id = child.id.get_value()
                    graph_name = child.name.get_value()
                # Modifying the flow rule to set the source mac_address
                if mac_address is not None and mac_address != 'undefined':
                    match_string = "source_mac=" + mac_address
                    logging.debug("Match string = " + match_string)
                    for newflowentry in newFlowtable:
                        if flag:
                            port_path = newflowentry.port.get_value()
                            logging.debug("Port: " + port_path)
                            tokens = port_path.split('/')
                            if tokens[1] == "virtualizer":
                                newflowentry.match.data = match_string
                                flag=False
                else:
                    Session().set_error(session_id)
                    logging.debug("Failed to instantiated profile for user '"+self.user_data.username+"': no mac provided")
                    print("Failed to instantiated profile for user '"+self.user_data.username+"'")
                    return
                # Call orchestrator to get the actual configuration -> only if mdo/escape/BiS-BiS node/diff == true
                '''
                logging.debug('Calling orchestrator getting actual configuration')
                try:
                    mdo_config = self.orchestrator.getNFFG()
                    logging.debug('Retrieved configuration: ')
                    logging.debug(mdo_config)
                except Exception as err:
                    logging.exception(err)
                    Session().set_error(session_id)
                    logging.debug("Failed to retrieve MdO configuration ")
                    raise err
                try:
                    original_tree = ET.ElementTree(ET.fromstring(mdo_config))
                    original_root = original_tree.getroot()
                except ET.ParseError as e:
                    print('ParseError: %s' % e.message)
                    logging.exception(e)
                    Session().set_error(session_id)
                    raise e

                #Parsing of the Mdo original configuration
                Infrastructure = Virtualizer.parse(root= original_root)
                Flowtable = Infrastructure.nodes.node['SingleBiSBiS'].flowtable
                NfInstances = Infrastructure.nodes.node['SingleBiSBiS'].NF_instances
                
                logging.debug("Istanza grafo %s -- %s", graph_id, graph_name)


                #Adding the user graph to the original configuration
                try:
                    for instance in newNfInstances:
                        NfInstances.add(instance)
                except Exception as err:
                    logging.exception(err)
                    Session().set_error(session_id)
                    logging.debug("Can't add the nf instance to the graph")
                try:
                    for flowentry in newFlowtable:
                        Flowtable.add(flowentry)
                except Exception as err:
                    loggin.exception(err)
                    Session().set_error(session_id)
                    logging.debug("Can't add the flowrule to the graph")
                logging.debug("Graph is going to be instantiated:")
                logging.debug(Infrastructure.xml())
                nffg= Infrastructure.xml()
                '''
                nffg = newInfrastructure.xml()
                #TODO eliminare il commento alla initialize session finito il debug. Bisogna anche tenere traccia degli id delle flowrule quando l'utente fa il logout
                #Session().inizializeSession(session_id, self.user_data.getUserID(), graph_id, graph_name)
        else:
            # Authentication graph
            logging.debug('Instantiating the authentication graph')
            logging.debug('Instantiate profile')
            session_id = uuid.uuid4().hex
            if nffg is not None:
                try:
                    tree = ET.ElementTree(ET.fromstring(nffg))
                    logging.debug("1--> %s", tree)
                    logging.debug("2--> %s", tree.getroot())
                    logging.debug("3--> %s %s", tree.getroot().tag, tree.getroot().attrib)
                    root = tree.getroot()
                    for child in root.findall("nodes"):
                        logging.debug("%s %s", child.tag, child.attrib)
                except ET.ParseError as e:
                    print('ParseError: %s' % e.message)
                    logging.exception(e)
                    Session().set_error(session_id)
                    raise e
                newInfrastructure = Virtualizer.parse(root=root)
                newFlowtable = newInfrastructure.nodes.node['SingleBiSBiS'].flowtable
                newNfInstances = newInfrastructure.nodes.node['SingleBiSBiS'].NF_instances
                for child in newNfInstances:
                    graph_id = child.id.get_value()
                    graph_name = child.name.get_value()
                logging.debug("Istanza grafo %s -- %s", graph_id, graph_name)
                #TODO eliminare il commento alla initialize session finito il debug.
                #Session().inizializeSession(session_id, self.user_data.getUserID(), graph_id, graph_name)

        # Call orchestrator to instantiate NF-FG
        logging.debug("Calling orchestrator to instantiate '"+self.user_data.username+"' forwarding graph.")
        if DEBUG_MODE is False:
            try:
                self.orchestrator.put(nffg)
                logging.debug("Profile instantiated for user '"+self.user_data.username+"'")
            except Exception as err:
                logging.exception(err)
                Session().set_error(session_id)
                logging.debug("Failed to instantiated profile for user '"+self.user_data.username+"'")
                print("Failed to instantiated profile for user '"+self.user_data.username+"'")
                raise err
        else:
            # debug mode
            logging.debug("DEBUG_MODE: Graph "+ graph_name  + " instantiated for user '"+self.user_data.username+"'")
            logging.debug(nffg)

def addFlows(self, nffg, location):
	logging.debug('Calling orchestrator getting actual configuration')
	try:
		mdo_config = self.orchestrator.getNFFG()
		logging.debug('Retrieved configuration: ')
		#logging.debug(mdo_config)
	except Exception as err:
		logging.exception(err)
		logging.debug("Failed to retrieve MdO configuration ")
		raise err
	try:
		new_tree = ET.ElementTree(ET.fromstring(nffg));
		new_root = new_tree.getroot()
	except ET.ParseError as e:
		print('ParseError: %s' % e.message)
		logging.exception(e)
		raise e
	newInfrastructure = Virtualizer.parse(root= new_root)
	newInstances = newInfrastructure.nodes.node['SingleBiSBiS'].NF_instances
	nf_id = 0
	for nf_inst in newInstances:
		nf_id = nf_inst.id.get_value() #take the first nf id to set the id of flowentries
		break

	try:
		original_tree = ET.ElementTree(ET.fromstring(mdo_config))
		original_root = original_tree.getroot()
	except ET.ParseError as e:
		print('ParseError: %s' % e.message)
		logging.exception(e)
		raise e
	#Parsing of the Mdo original configuration
	Infrastructure = Virtualizer.parse(root= original_root)
	Flowtable = Infrastructure.nodes.node['SingleBiSBiS'].flowtable
	NfInstances = Infrastructure.nodes.node['SingleBiSBiS'].NF_instances
	Ports = Infrastructure.nodes.node['SingleBiSBiS'].ports
	logging.debug('Port parsed:' + location)
	for port in Ports:
		logging.debug('port: ' + port.name.get_value())
		if port.name.get_value() in location:
			logging.debug('port found')
        	#port_id found
			id_port = port.id.get_value()
			id_flow1 = nf_id + str(1) #TODO da cambiare con un valore dinamico
			port_flow1 = '../../../NF_instances/node[id=' + nf_id + ']/ports/port[id=0]' #the port with id 0 is reserved to the flow added by the service layer 
			out_flow1 = '/virtualizer/nodes/node[id=SingleBiSBiS]/ports/port[id=' + id_port + ']'       
			id_flow2 = nf_id + str(2)
			port_flow2 = out_flow1
			out_flow2 = port_flow1
			filled_nffg = create_xml(id_flow1, port_flow1, out_flow1, id_flow2, port_flow2, out_flow2, nffg)
			return filled_nffg

def create_xml(id_flow1, port_flow1, out_flow1, id_flow2, port_flow2, out_flow2, nffg):
  	with open(".tmp_"+str(id_flow1), 'w') as outfile1:
  		#logging('Writing file: tmp_' + id_flow1)
   		outfile1.write(nffg);

   	with open(".tmp_"+str(id_flow1), 'r') as infile:
   		with open(".tmp_1"+str(id_flow1), 'w') as outfile:
   			flag = True
   			rowIter = iter(infile)
   			for row in rowIter:
   				if flag is True and 'flowentry' in row:

   					outfile.write('\t\t\t\t<flowentry operation=\"create\">\n')
   					outfile.write('\t\t\t\t\t<id>'+str(id_flow1)+'</id>\n')
   					outfile.write('\t\t\t\t\t<priority>100</priority>\n')
   					outfile.write('\t\t\t\t\t<port>'+port_flow1+'</port>\n')
   					outfile.write('\t\t\t\t\t<out>'+out_flow1+'</out>\n')
   					outfile.write('\t\t\t\t\t<resources>\n')
   					outfile.write('\t\t\t\t\t\t<bandwidth>0</bandwidth>\n')
   					outfile.write('\t\t\t\t\t</resources>\n')
   					outfile.write('\t\t\t\t</flowentry>\n')

   					outfile.write('\t\t\t\t<flowentry operation=\"create\">\n')
   					outfile.write('\t\t\t\t\t<id>'+str(id_flow2)+'</id>\n')
   					outfile.write('\t\t\t\t\t<priority>100</priority>\n')
   					outfile.write('\t\t\t\t\t<port>'+port_flow2+'</port>\n')
   					outfile.write('\t\t\t\t\t<out>'+out_flow2+'</out>\n')
   					outfile.write('\t\t\t\t\t<resources>\n')
   					outfile.write('\t\t\t\t\t\t<bandwidth>0</bandwidth>\n')
   					outfile.write('\t\t\t\t\t</resources>\n')
   					outfile.write('\t\t\t\t</flowentry>\n')
   					outfile.write('\t\t\t\t<flowentry operation=\"create\">\n')
   					flag = False
   				else:
   					outfile.write(row);
   	with open(".tmp_1"+str(id_flow1), 'r') as return_file:
   		return return_file.read()

