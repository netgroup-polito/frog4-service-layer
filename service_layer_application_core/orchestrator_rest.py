'''
Created on Jun 24, 2015

@author: fabiomignini
'''
import logging
import requests
#import json
import ast
from service_layer_application_core.config import Configuration
#from vnf_template_library.template import Template
#from vnf_template_library.validator import ValidateTemplate
#from nffg_library.nffg import NF_FG
#from nffg_library.validator import ValidateNF_FG

class GlobalOrchestrator(object):
    timeout = Configuration().ORCH_TIMEOUT
        
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        #self.user_data = user_data
        self.base_url = "http://"+str(ip)+":"+str(port)
        self.post_url = self.base_url+"/escape/edit-config"
        #self.delete_url = self.base_url+"/NF-FG/%s"
        self.get_url = self.base_url+"/escape/get-config"
        #self.get_status_url = self.base_url+"/NF-FG/status/%s"
        #self.get_template = self.base_url+"/template/location/%s"
        #self.headers = {'Content-Type': 'application/json',
        #                'cache-control': 'no-cache',
        #                'X-Auth-User': user_data.username,
        #                'X-Auth-Pass': user_data.password,
        #                'X-Auth-Tenant': user_data.tenant}
        self.headers = {'Content-Type': 'application/xml'}
    """
    def getTemplate(self, vnf_template_location):
        resp = requests.get(self.get_template % (vnf_template_location), headers=self.headers, timeout=int(self.timeout))
        resp.raise_for_status()
        template_dict = json.loads(resp.text)
        ValidateTemplate().validate(template_dict)
        template = Template()
        template.parseDict(template_dict)
        logging.debug("Get template from orchestrator completed")
        return template
    
    def getNFFGStatus(self, nffg_id):
        resp = requests.get(self.get_status_url % (nffg_id), headers=self.headers, timeout=int(self.timeout))
        logging.debug("HTTP response status code: " + str(resp.status_code))
        resp.raise_for_status()
        logging.debug("Check completed")
        # dict_resp = ast.literal_eval(resp.text)
        return resp.text
    """
    def getNFFG(self):
        resp = requests.get(self.get_url, timeout=int(self.timeout))
        resp.raise_for_status()
        #nffg_dict = json.loads(resp.text)
        #ValidateNF_FG().validate(nffg_dict)
        #nffg = NF_FG()
        #nffg.parseDict(nffg_dict)
        logging.debug("Get NFFG completed")
        return resp.text #return nffg
        
    def put(self, nffg):
        resp = requests.post(self.post_url,headers=self.headers, data=nffg, timeout=int(self.timeout))
        resp.raise_for_status()
        logging.debug("Post completed")
        return resp.text
    """
    def delete(self, nffg_id):
        resp = requests.delete(self.delete_url % (nffg_id), headers=self.headers, timeout=int(self.timeout))
        resp.raise_for_status()
        logging.debug("Delete completed")
        return resp.text
    """
