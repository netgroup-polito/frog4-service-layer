"""
Created on 19 Apr 2016

@author: gabrielecastellano
"""

from sqlalchemy import Column, VARCHAR, Integer
from sqlalchemy.ext.declarative import declarative_base
from service_layer_application_core.sql.sql_server import get_session
from service_layer_application_core.config import Configuration
from nffg_library.nffg import EndPoint

Base = declarative_base()
sql_server = Configuration().CONNECTION


class EndPointModel(Base):
    __tablename__ = 'end_point'
    attributes = ['id', 'name', 'node', 'type', 'domain_name', 'interface']
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(64))
    type = Column(VARCHAR(64))
    domain_name = Column(VARCHAR(64))
    interface = Column(VARCHAR(64))


class EndPointDB(object):
    def __init__(self):
        pass

    @staticmethod
    def add_end_point(name, _type, domain, interface):

        session = get_session()
        with session.begin():
            max_id = -1
            end_points_refs = session.query(EndPointModel).all()
            for end_point_ref in end_points_refs:
                if end_point_ref.id > max_id:
                    max_id = end_point_ref.id
            end_point = EndPointModel(
                id=max_id + 1,
                name=name,
                type=_type,
                domain_name=domain,
                interface=interface
            )
            session.add(end_point)
            return end_point.id

    @staticmethod
    def get_end_point(end_point_id):
        """

        :param end_point_id:
        :return:
        :rtype: EndPointModel
        """
        session = get_session()
        return session.query(EndPointModel).filter_by(id=end_point_id).one()
