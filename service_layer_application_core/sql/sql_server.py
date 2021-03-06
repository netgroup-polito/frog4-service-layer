"""
Created on Jun 22, 2015

@author: fabiomignini
"""
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from service_layer_application_core.config import Configuration

sqlserver = Configuration().DB_CONNECTION

def create_session():
    engine = sqlalchemy.create_engine(sqlserver)  # connect to server
    session = sessionmaker()
    session.configure(bind=engine,autocommit=True)
    return session()

def get_session():
    return create_session()