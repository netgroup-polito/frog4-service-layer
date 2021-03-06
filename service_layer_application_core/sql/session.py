'''
Created on Oct 1, 2014

@author: fabiomignini
'''
from sqlalchemy import Column, DateTime, func, VARCHAR, Text, not_, desc
from service_layer_application_core.sql.sql_server import get_session
from sqlalchemy.ext.declarative import declarative_base
from service_layer_application_core.exception import SessionNotFound


import datetime
import logging

Base = declarative_base()

class SessionModel(Base):
    '''
    Maps the database table session
    '''
    __tablename__ = 'session'
    attributes = ['id', 'user_id', 'service_graph_id', 'service_graph_name', 'ingress_node', 'egress_node', 'status',
                  'started_at', 'last_update', 'error', 'ended']
    id = Column(VARCHAR(64), primary_key=True)
    user_id = Column(VARCHAR(64))
    service_graph_id = Column(Text)
    service_graph_name = Column(Text)
    ingress_node = Column(Text)
    egress_node = Column(Text)
    status = Column(Text)
    started_at = Column(Text)
    last_update = Column(DateTime, default=func.now())
    error = Column(Text)
    ended = Column(DateTime)
    
 
class UserDeviceModel(Base):
    '''
    Maps the database table user_device
    '''
    __tablename__ = 'user_device'
    attributes = ['session_id', 'mac_address', 'endpoint_id', 'endpoint_db_id']
    session_id = Column(VARCHAR(64), primary_key=True)
    mac_address = Column(VARCHAR(64), primary_key=True)
    endpoint_id = Column(VARCHAR(64))
    endpoint_db_id = Column(VARCHAR(64))

class Session(object):
    def __init__(self):
        pass
    
    def inizializeSession(self, session_id, user_id, service_graph_id, service_graph_name):
        """
        initialize the session in db
        """
        session = get_session()  
        with session.begin():
            session_ref = SessionModel(id=session_id, user_id=user_id, service_graph_id=service_graph_id,
                                       started_at=datetime.datetime.now(), service_graph_name=service_graph_name,
                                       last_update=datetime.datetime.now(), status='inizialization')
            session.add(session_ref)
        pass

    def updateStatus(self, session_id, status, ended=True):
        session = get_session()  
        with session.begin():
            res = session.query(SessionModel)\
                .filter_by(id=session_id)\
                .filter_by(error=None)
            if not ended:
                res = res.filter_by(ended=None)
            res.update({"last_update":datetime.datetime.now(), 'status': status})

    def updateUserID(self, session_id, user_id):
        session = get_session()
        with session.begin():
            session.query(SessionModel)\
                .filter_by(id=session_id)\
                .filter_by(ended=None)\
                .filter_by(error=None)\
                .update({"user_id": user_id})
    
    def updateSessionNode(self, session_id, ingress_node, egress_node):
        """
        store the session in db
        """
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(id = session_id).filter_by(ended = None).filter_by(error = None).update({"last_update":datetime.datetime.now(), "ingress_node":ingress_node, "egress_node": egress_node})
    
    def updateSession(self, session_id, ingress_node, egress_node, status):
        """
        store the session in db
        """
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(id = session_id).filter_by(ended = None).filter_by(error = None).update({"last_update":datetime.datetime.now(), "ingress_node":ingress_node, "egress_node": egress_node, 'status':status})
                
    '''   
    def update_session(self, service_graph_id, profile, infrastructure):
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(service_graph_id = service_graph_id).filter_by(ended = None).filter_by(error = None).update({"last_update":datetime.datetime.now()})
    '''
            
    def get_active_user_session(self, user_id):
        """
        returns if exists an active session of the user
        """
        session = get_session()
        session_ref = session.query(SessionModel)\
            .filter_by(user_id=user_id)\
            .filter_by(ended=None)\
            .filter_by(error=None)\
            .first()
        if session_ref is None:
            raise SessionNotFound("Session Not Found")
        return session_ref
    
    def get_active_user_device_session(self, user_id, mac_address=None, error_aware=True):
        """
        returns if exists an active session of the user connected on the port of the switch passed

        :param user_id: the id of the user in database.
        :param mac_address: if specified, search for this device in the session and raise if is not present.
        :param error_aware: if passed as "False", include also sessions that have "error" column setted.
        :return the number of devices for this user and the active session.
        :raise SessionNotFound if user haven't active session or if the specified device is not in the session.

        """
        session = get_session()
        if error_aware is True:
            user_session = session.query(SessionModel)\
                .filter_by(user_id=user_id)\
                .filter_by(ended=None)\
                .filter_by(error=None)\
                .first()
        else:
            user_session = session.query(SessionModel)\
                .filter_by(user_id=user_id)\
                .filter_by(ended=None)\
                .first()

        if user_session is None:
            raise SessionNotFound("Session Not Found")

        if mac_address is None:
            return 1, user_session
        else:
            # search for the specified device in this session
            logging.debug("MAC address: " + str(mac_address))
            devices = session.query(UserDeviceModel).filter_by(session_id=user_session.id).all()
            for device in devices:
                logging.debug("device MAC address:"+str(device.mac_address)+" MAC address:"+str(mac_address))
                if device.mac_address == mac_address:
                    return len(devices), user_session
            raise SessionNotFound("Device not found in the user session")

    def get_user_device(self, user_id, mac_address):
        """

        :param user_id:
        :param mac_address:
        :return:
        :rtype: UserDeviceModel
        """
        session = get_session()
        # get user session
        user_session = session.query(SessionModel)\
            .filter_by(user_id=user_id)\
            .filter_by(ended=None)\
            .filter_by(error=None)\
            .first()

        user_device = session.query(UserDeviceModel)\
            .filter_by(session_id=user_session.id)\
            .filter_by(mac_address=mac_address)\
            .one()
        return user_device

    def delete_user_devices_for_session(self, session_id):

        session = get_session()
        session.query(UserDeviceModel)\
            .filter_by(session_id=session_id)\
            .delete()

    def delete_user_device_for_session(self, session_id, mac_address):

        session = get_session()
        session.query(UserDeviceModel)\
            .filter_by(session_id=session_id)\
            .filter_by(mac_address=mac_address)\
            .delete()

    def set_ended(self, session_id):
        """
        Set the ended status for the session identified with session_id
        """
        session = get_session() 
        with session.begin():       
            session.query(SessionModel)\
                .filter_by(id=session_id)\
                .update({"ended": datetime.datetime.now()}, synchronize_session=False)
    
    def set_error_by_nffg_id(self, nffg_id):
        """
        Set the error status for the active session associated to the nffg id passed
        """
        session = get_session()
        with session.begin():     
            logging.debug("Put session for nffg "+str(nffg_id)+" in error")
            session.query(SessionModel).filter_by(service_graph_id=nffg_id).filter_by(ended = None).filter_by(error = None).update({"error":datetime.datetime.now()}, synchronize_session = False)
        
    def set_error(self, session_id):
        """
        Set the error status for the active session associated to the user id passed
        """
        session = get_session()
        with session.begin():
            logging.debug("Put session for session "+str(session_id)+" in error")
            session.query(SessionModel).filter_by(id=session_id).filter_by(ended = None).filter_by(error = None).update({"error":datetime.datetime.now()}, synchronize_session = False)
    
    def checkSession(self, user_id):
        """
        return true if there is already an active session of the user
        """
        session = get_session()
        user_session = session.query(SessionModel).filter_by(user_id = user_id).filter_by(ended = None).filter_by(error = None).first()
        if user_session is None:
            return False
        else:
            return True
        
    def checkDeviceSession(self, user_id, mac_address):
        """
        return true if there is already an active session of the user with this mac
        """
        session = get_session()
        user_sessions = session.query(SessionModel)\
            .filter_by(user_id=user_id)\
            .filter_by(ended=None)\
            .filter_by(error=None).all()
        for user_session in user_sessions:
            devices = session.query(UserDeviceModel).filter_by(session_id=user_session.id).all()
            for device in devices:
                if device.mac_address == mac_address:
                    return True
        return False
        
    @staticmethod
    def add_device_in_the_session(mac_address, endpoint_id, endpoint_db_id, session_id):
        session = get_session()
        with session.begin():     
            user_device_ref = UserDeviceModel(
                session_id=session_id,
                mac_address=mac_address,
                endpoint_db_id=endpoint_db_id,
                endpoint_id=endpoint_id
            )
            session.add(user_device_ref)

    @staticmethod
    def get_active_user_devices(user_id):
        session = get_session()
        user_sessions = session.query(SessionModel.id)\
            .filter_by(user_id=user_id)\
            .filter_by(ended=None)\
            .filter_by(error=None)\
            .all()
        user_devices = []
        for user_session in user_sessions:
            devices = session.query(UserDeviceModel).filter_by(session_id=user_session.id).all()
            for device in devices:
                user_devices.append(device)
        return user_devices

    def get_active_user_devices_for_endpoint(self, user_id, endpoint_id):
        """

        :param user_id:
        :param endpoint_id:
        :return:
        :rtype: list of UserDeviceModel
        """
        session = get_session()
        # get user session
        user_session = session.query(SessionModel)\
            .filter_by(user_id=user_id)\
            .filter_by(ended=None)\
            .filter_by(error=None)\
            .first()

        user_devices = session.query(UserDeviceModel)\
            .filter_by(session_id=user_session.id)\
            .filter_by(endpoint_id=endpoint_id)\
            .all()
        return user_devices

    def get_active_user_session_from_id(self, session_id):
        session = get_session()
        with session.begin():  
            user_session = session.query(SessionModel).filter_by(id=session_id).filter_by(ended = None).filter_by(error = None).first()
            if not user_session:
                raise SessionNotFound("Session Not Found") 
        return user_session
    
    def get_active_user_session_by_nf_fg_id(self, service_graph_id, error_aware=True):
        session = get_session()
        if error_aware:
            session_ref = session.query(SessionModel).filter_by(service_graph_id = service_graph_id).filter_by(ended = None).filter_by(error = None).first()
        else:
            session_ref = session.query(SessionModel).filter_by(service_graph_id = service_graph_id).filter_by(ended = None).order_by(desc(SessionModel.started_at)).first()
        if session_ref is None:
            raise SessionNotFound("Session Not Found, for servce graph id: "+str(service_graph_id))
        return session_ref
    
    def get_profile_id_from_active_user_session(self, user_id):
        session = get_session()
        session_ref = session.query(SessionModel.service_graph_id).filter_by(user_id = int(user_id)).filter_by(ended = None).filter_by(error = None).first()
        
        if session_ref is None:
            raise SessionNotFound("Session Not Found")
        return session_ref.service_graph_id
    
    def get_service_graph_info(self, session_id):
        session = get_session()
        return session.query(SessionModel.service_graph_id, SessionModel.service_graph_name).filter_by(id=session_id).one()
        
        
    def checkEgressNode(self, node, profile):
        """
        Return False if the only ingress point in the node
        is that that we are deleting
        """
        session = get_session()
        egs = session.query(SessionModel).filter_by(egress_node = node).filter(not_(Session.profile.contains(profile))).all()
        if egs is not None and len(egs) == 0:
            return False
        return True 

    def checkIngressNode(self, node, profile):
        """
        Return False if the only ingress point in the node
        is that that we are deleting
        """
        session = get_session()
        ings = session.query(SessionModel).filter_by(ingress_node = node).filter(not_(Session.profile.contains(profile))).all()
        if ings is not None and len(ings) == 0:
            return False
        return True