"""
Created on 01 dic 2015

@author: gabrielecastellano
@author: stefanopetrangeli
"""

from sqlalchemy import Column, VARCHAR, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from service_layer_application_core.sql.sql_server import get_session
from service_layer_application_core.config import Configuration
from service_layer_application_core.domain_info import DomainInfo, GreTunnel, Interface, Neighbor
from sqlalchemy.sql import func
from sqlalchemy.orm.exc import NoResultFound

from service_layer_application_core.sql.domain import DomainModel

Base = declarative_base()
sql_server = Configuration().CONNECTION


class DomainsInformationModel(Base):
    __tablename__ = 'domain_information'
    attributes = ['id', 'domain_id', 'node', 'interface', 'interface_type', 'gre', 'vlan']
    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer)
    node = Column(Integer)
    interface = Column(VARCHAR(64))
    interface_type = Column(VARCHAR(64))
    gre = Column(Boolean())
    vlan = Column(Boolean())


class DomainsGreModel(Base):
    __tablename__ = 'domain_gre'
    attributes = ['id', 'name', 'domain_info_id', 'local_ip', 'remote_ip', 'gre_key']
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(64))
    domain_info_id = Column(Integer)
    local_ip = Column(VARCHAR(64))
    remote_ip = Column(VARCHAR(64))
    gre_key = Column(VARCHAR(64))


class DomainsNeighborModel(Base):
    __tablename__ = 'domain_neighbor'
    attributes = ['id', 'domain_info_id', 'neighbor_domain_name', 'neighbor_node', 'neighbor_interface']
    id = Column(Integer, primary_key=True)
    domain_info_id = Column(Integer)
    neighbor_domain_name = Column(VARCHAR(64))
    neighbor_node = Column(VARCHAR(64))
    neighbor_interface = Column(VARCHAR(64))


class DomainInformation(object):
    def __init__(self):
        pass

    @staticmethod
    def get_domain_info(domain_name=None):
        session = get_session()
        domains_info_list = {}
        if domain_name is not None:
            pass
        else:
            domains_refs = session.query(DomainsInformationModel).all()
            for domain_ref in domains_refs:
                if domain_ref.domain_id not in domains_info_list:
                    domain_type = session.query(DomainModel).filter_by(id=domain_ref.domain_id).one().type
                    domain_info = DomainInfo(domain_id=domain_ref.domain_id, _type=domain_type)
                    domains_info_list[domain_ref.domain_id] = domain_info
                else:
                    domain_info = domains_info_list[domain_ref.domain_id]

                interface = Interface(node=domain_ref.node, name=domain_ref.interface, _type=domain_ref.interface_type,
                                      gre=domain_ref.gre, vlan=domain_ref.vlan)
                if interface.gre is True:
                    gre_refs = session.query(DomainsGreModel).filter_by(domain_info_id=domain_ref.id).all()
                    for gre_ref in gre_refs:
                        gre_tunnel = GreTunnel(name=gre_ref.name, local_ip=gre_ref.local_ip,
                                               remote_ip=gre_ref.remote_ip, gre_key=gre_ref.gre_key)
                        interface.addGreTunnel(gre_tunnel)

                neighbor_refs = session.query(DomainsNeighborModel).filter_by(domain_info_id=domain_ref.id).all()
                for neighbor_ref in neighbor_refs:
                    neighbor = Neighbor(domain_name=neighbor_ref.neighbor_domain_name, node=neighbor_ref.neighbor_node,
                                        interface=neighbor_ref.neighbor_interface)
                    interface.addNeighbor(neighbor)

                domain_info.addInterface(interface)
        return domains_info_list

    @staticmethod
    def get_domain_info_by_interface(domain_id, interface):
        """

        :param domain_id:
        :param interface:
        :return:
        :rtype: DomainsInformationModel
        """
        session = get_session()
        domain_info = session.query(DomainsInformationModel).filter_by(domain_id=domain_id, interface=interface).first()
        return domain_info

    @staticmethod
    def get_domain_id_from_node(node):
        session = get_session()
        with session.begin():
            domain = session.query(DomainsInformationModel).filter_by(node=node).first()
            if domain is None:
                return None
            return domain.domain_id

    @staticmethod
    def get_node_by_interface(domain_id, interface):
        """

        :param domain_id:
        :param interface:
        :return:
        :rtype: str
        """
        session = get_session()
        with session.begin():
            domain = session.query(DomainsInformationModel)\
                .filter_by(domain_id=domain_id)\
                .filter_by(interface=interface)\
                .first()
            if domain is None:
                return None
            return domain.node

    def add_domain_info(self, domain_info, update=False):
        """
        Populate domain_* tables on the DB.
        :param update: if is False domains information related to this domain_info are overwritten
        :param domain_info: the structure containing domain information
        """
        session = get_session()
        with session.begin():
            if update is False:
                try:
                    domain_refs = session.query(DomainsInformationModel).filter_by(
                        domain_id=domain_info.domain_id).all()
                    for domain_ref in domain_refs:
                        session.query(DomainsInformationModel).filter_by(id=domain_ref.id).delete()
                        session.query(DomainsGreModel).filter_by(domain_info_id=domain_ref.id).delete()
                        session.query(DomainsNeighborModel).filter_by(domain_info_id=domain_ref.id).delete()
                except NoResultFound:
                    pass
            self.id_generator(domain_info)
            for interface in domain_info.interfaces:
                info_ref = DomainsInformationModel(id=self.info_id, domain_id=domain_info.domain_id,
                                                   node=interface.node, interface=interface.name,
                                                   interface_type=interface.type, gre=interface.gre,
                                                   vlan=interface.vlan)
                session.add(info_ref)
                for neighbor in interface.neighbors:
                    neighbor_ref = DomainsNeighborModel(id=self.neighbor_id, domain_info_id=self.info_id,
                                                        neighbor_domain_name=neighbor.domain_name,
                                                        neighbor_node=neighbor.node,
                                                        neighbor_interface=neighbor.interface)
                    session.add(neighbor_ref)
                    self.neighbor_id += 1
                for gre_tunnel in interface.gre_tunnels:
                    gre_ref = DomainsGreModel(id=self.gre_id, name=gre_tunnel.name, domain_info_id=self.info_id,
                                              local_ip=gre_tunnel.local_ip, remote_ip=gre_tunnel.remote_ip,
                                              gre_key=gre_tunnel.gre_key)
                    session.add(gre_ref)
                    self.gre_id += 1

                self.info_id += 1

    def id_generator(self, domain_info):
        info_base_id = self._get_higher_info_id()
        gre_base_id = self._get_higher_gre_id()
        neighbor_base_id = self._get_higher_neighbor_id()
        if info_base_id is not None:
            self.info_id = int(info_base_id) + 1
        else:
            self.info_id = 0
        if gre_base_id is not None:
            self.gre_id = int(gre_base_id) + 1
        else:
            self.gre_id = 0
        if neighbor_base_id is not None:
            self.neighbor_id = int(neighbor_base_id) + 1
        else:
            self.neighbor_id = 0

    @staticmethod
    def _get_higher_info_id():
        session = get_session()
        return session.query(func.max(DomainsInformationModel.id).label("max_id")).one().max_id

    @staticmethod
    def _get_higher_gre_id():
        session = get_session()
        return session.query(func.max(DomainsGreModel.id).label("max_id")).one().max_id

    @staticmethod
    def _get_higher_neighbor_id():
        session = get_session()
        return session.query(func.max(DomainsNeighborModel.id).label("max_id")).one().max_id

    @staticmethod
    def get_domain_gre(domain_gre_id):
        """

        :param domain_gre_id:
        :return:
        :rtype: DomainsGreModel
        """
        session = get_session()
        return session.query(DomainsGreModel).filter_by(id=domain_gre_id).one()

    @staticmethod
    def add_domain_gre(domain_name, domain_info_id, local_ip, remote_ip, gre_key, domain_gre_id=None):
        session = get_session()

        with session.begin():
            if domain_gre_id is not None:
                _id = domain_gre_id
                domain_gre_refs = session.query(DomainsGreModel).all()
                for domain_gre_ref in domain_gre_refs:
                    if domain_gre_ref.id == domain_gre_id:
                        # TODO create an exception
                        raise Exception
            else:
                max_id = -1
                domain_gre_refs = session.query(DomainsGreModel).all()
                for domain_gre_ref in domain_gre_refs:
                    if domain_gre_ref.id > max_id:
                        max_id = domain_gre_ref.id
                    if domain_gre_ref.domain_info_id == domain_info_id:
                        return domain_gre_ref.id
                _id = max_id+1
            domain_gre = DomainsGreModel(
                id=_id,
                name=domain_name,
                domain_info_id=domain_info_id,
                local_ip=local_ip,
                remote_ip=remote_ip,
                gre_key=gre_key
            )
            session.add(domain_gre)
            return domain_gre.id
