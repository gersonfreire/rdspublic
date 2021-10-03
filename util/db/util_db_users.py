#!/usr/bin/env python3.7

""" 
Gerenciamento de usuários
"""

import sys
import os 
import logging
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.log import instance_logger
from sqlalchemy.sql.expression import true
from sqlalchemy.sql.sqltypes import DECIMAL

# Assume diretorio atual do script para encontrar arquivo do banco de dados
path = os.path.dirname(os.path.abspath(__file__)) 
db_file = os.path.basename(os.path.abspath(__file__)).split('.')[0]

# banco de dados único
# banco de dados separado por admin do bot
bot_admin = None
if len(sys.argv) > 1:
    bot_admin = sys.argv[2]
db_file_admin = f'_{str(bot_admin)}' if bot_admin else ''
db_file_full_path = f'{path}{os.sep}config_{db_file}{db_file_admin}.db'

engine = create_engine(f'sqlite:///{db_file_full_path}', echo=True)

from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session:sqlalchemy.orm.session.Session = Session()

# criar tabelas
from sqlalchemy.ext.declarative import declarative_base

# Declare a Mapping
Base = declarative_base()

from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True)
    user_name = Column(String)
    phone = Column(String)
    # tlg_user_serialized = Column(String)
    rdstation_id = Column(Integer)
    rdstation_token = Column(String)
    # parent_bot_user_id = Column(Integer)
    balance = Column(DECIMAL)

    def __repr__(self):
        return f'User {self.name}'

Base.metadata.create_all(engine)

def get_all():
    try:
        query = session.query(User) 
        return query.all()
    except Exception as e:
        logging.error(str(e))     

def get_user_by_id(chat_id:int):
    try:
        query = session.query(User).filter_by(chat_id=chat_id)
        return query.all()
    except Exception as e:
        logging.error(str(e))
        
def upd_user_by_id(chat_id:int, rdstation_token:str):
    try:
        query = session.query(User).filter_by(chat_id=chat_id)
        user_list = query.all()
        if len(user_list) > 0:
            user_list[0].rdstation_token = rdstation_token
            session.commit()
            
    except Exception as e:
        logging.error(str(e))
        
def examples():
    # Fazendo buscas https://docs.sqlalchemy.org/en/14/orm/tutorial.html
    query = session.query(User) # .filter_by(name='')
    query.count()
    all_users = query.all()

    # Adicionando novos usuários
    user = User(chat_id=1, user_name='John Snow')
    session.add(user)
    session.commit()

    #Equivalent to 'SELECT * FROM census'
    # query = sqlalchemy.select([census])
    metadata = sqlalchemy.MetaData()
    users = sqlalchemy.Table('users', metadata, autoload=True, autoload_with=engine)
    #Equivalent to 'SELECT * FROM census'
    query = sqlalchemy.select([users])

    connection = engine.connect()
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    ResultSet[:1]

# ---------------------------
# Teste unitário
def unit_test():
    try:
        chat_id = sys.argv[2]
        user_by_id = get_user_by_id(chat_id)
        
        upd_user_by_id(chat_id, '')
        
        rdstation_token = sys.argv[3]
        upd_user_by_id(chat_id, rdstation_token)
        
        all_users = get_all()
        each_user:User
        for each_user in all_users:
            logging.debug(each_user.user_name)
            each_user.rdstation_token = 'ssdd'
        
        session.commit()
        
    except Exception as e:
        logging.error(str(e))    

if __name__ == '__main__':
    unit_test() 

logging.debug(f'FIM import {__file__}')