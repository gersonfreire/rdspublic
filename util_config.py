#!/usr/bin/env python3.7

# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
# type: ignore[union-attr]

"""
Módulo de funções de configuração.

Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

# módulos acesso banco de dados SQLite
# pip3 install pysqlite3
import sqlite3
from sqlite3 import Error

import os
import logging

# Nome padrão do arquivo de configuração
config_default_file = 'config' # .db'

# --- Acesso a banco de dados
# def execute_query(query: str, db_file:str = config_default_file) -> []:
def execute_query(query: str, db_file:str = None) -> []:

    try:
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Assume diretorio atual do script para encontrar arquivo do banco de dados
        path = os.path.dirname(os.path.abspath(__file__))   
        if db_file is None:
            db_file = f'{path}{os.sep}{config_default_file}'
        else:
            db_file = f'{path}{os.sep}{db_file}'
            
        conn = sqlite3.connect(db_file)
        logging.info("Conectado com sucesso ao banco de dados %s (versão %s)"%(db_file, sqlite3.version))   

        curs=conn.cursor()
        rows = curs.execute(query)
        conn.commit()

        all_rows = rows.fetchall() 
        
        return all_rows

    except Exception as e:
        logging.info("execute_query: " + str(e))

# --- Obtem todos os usuarios cadastrados

def get_all_users(limit_to:int = 0, filter:str=None) -> []:
    try:
        query = 'SELECT * FROM users'

        if filter is not None:
            query += f' WHERE {filter} '

        if (limit_to == 0) and (filter is None):
            all_rows = execute_query(query = query)
        else:
            all_rows = execute_query(query = f'{query} LIMIT {limit_to}')        
        
        return all_rows

    except Exception as e:
        logging.info("util_config: " + str(e))   
        return False 

def get_all_users_cache() -> {}:

    users_cache = {}

    try:
        all_rows = execute_query(query = 'SELECT * FROM users')
        if len(all_rows) > 0:
            for row in all_rows:
                # subscribers_list.append(row[1])  
                users_cache[row[1]] = row[2]
                logging.debug(row)                 

    except Exception as e:
        logging.info("util_config: " + str(e))   
    
    return users_cache            

def get_all_users_id_name(limit_to:int = 0) -> {}:
       
    user_id_names = {}

    try:
        all_rows = get_all_users(limit_to)

        # selected_elements = [all_rows[index] for index in indices]

        if len(all_rows) > 0:
            for row in all_rows:
                # subscribers_list.append(row[1])   
                # users_cache[row[1]] = row[2]
                # user_id_names = row[1:]
                # user_id_names.append(row[1:])
                user_id_names[row[1]] = row[2]
                logging.info(row[1:]) 

    except Exception as e:
        logging.info("util_config: " + str(e))   

    return user_id_names 

# ---- Salva usuários cadastrados

def save_all_users(all_rows : []) -> bool:

    try:
        if len(all_rows) > 0:
            for row in all_rows:
                save_user(row)
                logging.info(row[1:]) 

        return True

    except Exception as e:
        logging.info("util_config: " + str(e))   
        return False     
  
def save_user(row : []) -> bool:

    try:
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Assume diretorio atual do script para encontrar arquivo do banco de dados
        path = os.path.dirname(os.path.abspath(__file__))   
        db_file = path + "/config.db"
        conn = sqlite3.connect(db_file)
        logging.info("Conectado com sucesso ao banco de dados %s (versão %s)"%(db_file, sqlite3.version)) 

        chat_id = row[1]
        user_name = row [2]

        curs=conn.cursor()

        query = "INSERT INTO users (chat_id, user_name) VALUES(%d, '%s')"%(chat_id, user_name)
        curs.execute(query)

        conn.commit()  

        logging.debug("Usuario inserido com sucesso: %d %s"%(chat_id, user_name)) 

        curs.close()
        conn.close()         
    
        return True

    except Exception as e:
        logging.info("execute_query: " + str(e))   
        return False 

def save_user2(user_id: int, user_name: str, db_file:str = None) -> bool:

    try:
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Assume diretorio atual do script para encontrar arquivo do banco de dados
        path = os.path.dirname(os.path.abspath(__file__)) 
        if db_file is None:  
            db_file = path + os.sep + "config.db"
        else:
            db_file = f'{path}{os.sep}{db_file}'
        conn = sqlite3.connect(db_file)
        logging.info("Conectado com sucesso ao banco de dados %s (versão %s)"%(db_file, sqlite3.version)) 

        chat_id = user_id
        user_name = user_name

        curs=conn.cursor()

        query = "INSERT INTO users (chat_id, user_name) VALUES(%d, '%s')"%(chat_id, user_name)
        curs.execute(query)

        conn.commit()  

        logging.debug("Usuario inserido com sucesso: %d %s"%(chat_id, user_name)) 

        curs.close()
        conn.close()         
    
        return True

    except Exception as e:
        logging.error(str(e))   
        return False 

def save_user_rdstation(user_id: int, user_name: str, db_file:str = None, rdstation_token:str = None) -> bool:

    try:
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Assume diretorio atual do script para encontrar arquivo do banco de dados
        path = os.path.dirname(os.path.abspath(__file__)) 
        if db_file is None:  
            db_file = path + os.sep + "config.db"
        else:
            db_file = f'{path}{os.sep}{db_file}'
        conn = sqlite3.connect(db_file)
        logging.info("Conectado com sucesso ao banco de dados %s (versão %s)"%(db_file, sqlite3.version)) 

        chat_id = user_id
        user_name = user_name

        curs=conn.cursor()

        if rdstation_token is None:
            rdstation_token = ''

        # Sempre tenta criar o campo de token do RDStation
        execute_query(f'alter table users add column rdstation_token text;')

        try:
            query = f"UPDATE users set rdstation_token = '{rdstation_token}' WHERE chat_id = {chat_id} " 
            execute_query(query=query)  
        except Exception as e:
                logging.error(str(e))              

        #no such column: rdstation_token
        query = f"INSERT INTO users (chat_id, user_name, rdstation_token) VALUES({chat_id}, '{user_name}', '{rdstation_token}')" 

        execute_query(query=query)

        logging.debug("Usuario inserido com sucesso: %d %s"%(chat_id, user_name)) 

        curs.close()
        conn.close()         
    
        return True

    except Exception as e:
        logging.error(str(e))   
        return False 

def get_rdstation_token(user_id: int, db_file:str = None) -> str:

    rdstation_token = None

    try:
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Assume diretorio atual do script para encontrar arquivo do banco de dados
        path = os.path.dirname(os.path.abspath(__file__)) 
        if db_file is None:  
            db_file = path + os.sep + "config.db"
        else:
            db_file = f'{path}{os.sep}{db_file}'
        conn = sqlite3.connect(db_file)
        logging.info("Conectado com sucesso ao banco de dados %s (versão %s)"%(db_file, sqlite3.version)) 

        chat_id = user_id

        curs=conn.cursor()

        query = f"SELECT rdstation_token FROM users WHERE chat_id = {chat_id} " 
        all_rows = execute_query(query = query)   
        if len(all_rows) > 0:
            rdstation_token = all_rows[0][0]

        if rdstation_token == '':
            rdstation_token = None                  

        logging.debug("token obtido com sucesso: %d"%(chat_id)) 

        curs.close()
        conn.close()  

    except Exception as e:
        logging.error(str(e))   
    
    return rdstation_token

# ---------- Testes unitarios -----------

def main():
    all_rows = get_all_users()

    user_id_names = get_all_users_id_name()

    print(user_id_names)

    save_all_users(all_rows)

if __name__ == '__main__':
    main() 


#  ------------ Exemplos manipulação de tuplas 

# L = ['a', 'b', 'c', 'd', 'e', 'f']
# print [ L[index] for index in [1,3,5] ]

# sek=[]
# L=[1,2,3,4,5,6,7,8,9,0]
# for i in [2, 4, 7, 0, 3]:
#    a=[L[i]]
#    sek=sek+a
# print (sek)

# a_list = [1, 2, 3]
# indices = [0, 2]

# Slice of Lists
# z = [3, 7, 4, 2]
# print(z[0:2])

"""
countries = [
    ['China', 1394015977],
    ['United States', 329877505],
    ['India', 1326093247],
    ['Indonesia', 267026366],
    ['Bangladesh', 162650853],
    ['Pakistan', 233500636],
    ['Nigeria', 214028302],
    ['Brazil', 21171597],
    ['Russia', 141722205],
    ['Mexico', 128649565]
]

populated = filter(lambda c: c[1] > 300000000, countries)

print(list(populated))
"""