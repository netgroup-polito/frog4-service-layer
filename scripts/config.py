'''
Created on Oct 1, 2014
@author: fabiomignini
'''
import configparser
import inspect
import os


class Configuration(object):

    _instance = None
    #(fmignini) Not too meaningful use this var, I should change his name with something else like inizialized = False
    _AUTH_SERVER = None

    def __new__(cls, *args, **kwargs):

        if not cls._instance:
            cls._instance = super(Configuration, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if self._AUTH_SERVER is None:
            self.inizialize()

    def inizialize(self):
        config = configparser.RawConfigParser()
        base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])).rpartition('/')[0]
        config.read(base_folder+'/config/demo_frog4.ini')
        self._DD_CUSTOMER = config.get('doubledecker', 'dd_customer')
        self._BROKER_ADDRESS = config.get('doubledecker', 'broker_address')
        self._DD_KEYFILE = config.get('doubledecker', 'dd_keyfile')

    @property
    def BROKER_ADDRESS(self):
        return self._BROKER_ADDRESS

    @property
    def DD_CUSTOMER(self):
        return self._DD_CUSTOMER

    @property
    def DD_KEYFILE(self):
        return self._DD_KEYFILE