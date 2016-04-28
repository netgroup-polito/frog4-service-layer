"""
Created on Apr 12, 2016

@author: gabrielecastellano
"""

from sqlalchemy import Column, VARCHAR, Integer
from sqlalchemy.ext.declarative import declarative_base
import logging
from service_layer_application_core.exception import DomainNotFound
from service_layer_application_core.sql.sql_server import get_session

Base = declarative_base()


class DomainModel(Base):
    """
    Maps the database table Domain
    """
    __tablename__ = 'domain'
    attributes = ['id', 'name', 'type']
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(64))
    type = Column(VARCHAR(64))


class Domain(object):
    def __init__(self):
        pass

    @staticmethod
    def get_domain(domain_id):
        """

        :param domain_id:
        :return:
        :rtype: DomainModel
        """
        session = get_session()
        try:
            return session.query(DomainModel).filter_by(id=domain_id).one()
        except Exception as ex:
            logging.error(ex)
            raise DomainNotFound("Domain not found: " + str(domain_id)) from None

    @staticmethod
    def get_domain_from_name(name):
        """

        :param name:
        :return:
        :rtype: DomainModel
        """
        session = get_session()
        try:
            return session.query(DomainModel).filter_by(name=name).one()
        except Exception as ex:
            logging.error(ex)
            raise DomainNotFound("Domain not found for name: " + str(name)) from None

    @staticmethod
    def add_domain(domain_name, domain_type):
        session = get_session()
        with session.begin():
            max_id = -1
            domain_refs = session.query(DomainModel).all()
            for domain_ref in domain_refs:
                if domain_ref.id > max_id:
                    max_id = domain_ref.id
                if domain_ref.name == domain_name and domain_ref.type == domain_type:
                    return domain_ref.id
            domain = DomainModel(id=max_id + 1, name=domain_name, type=domain_type)
            session.add(domain)
            return domain.id
