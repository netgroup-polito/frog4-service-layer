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
        self.base_url = "http://"+str(ip)+":"+str(port)
        self.post_url = self.base_url+"/escape/edit-config"
        self.get_url = self.base_url+"/escape/get-config"
        self.headers = {'Content-Type': 'application/xml'}

    def getNFFG(self):
        resp = requests.post(self.get_url, timeout=int(self.timeout))
        resp.raise_for_status()
        logging.debug("Get NFFG completed")
        return resp.text #return nffg
        
    def post(self, nffg):
        resp = requests.post(self.post_url,headers=self.headers, data=nffg, timeout=int(self.timeout))
        resp.raise_for_status()
        logging.debug("Post completed")
        return resp.text

