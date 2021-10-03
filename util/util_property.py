from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler)
import telegram
import logging
import socket
import subprocess
import os
import sys
import requests
import configparser
from pathlib import Path
import re
from datetime import datetime

import bot_config

version = '1.1.0'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

script_path = os.path.dirname(os.path.abspath(__file__)) 
# script_path = os.path.dirname(__file__)
script_name = os.path.basename(sys.argv[0])
root, ext = os.path.splitext(script_name)

# procura arquivo de propriedades na pasta prop local
bot_properties_file = f'{script_path}{os.sep}prop/{root}.properties' if bot_config.bot_client is None else f'{script_path}{os.path.sep}{bot_name}.properties'

try:
    if os.path.isfile(f'{bot_properties_file}'):
        logging.info(f"Using {bot_properties_file}")
        config = configparser.ConfigParser()
        config.read(bot_properties_file)
        token = config['bot_config']['token']
        # handle = config['bot_config']['handle']
        # db_file = config['bot_config']['db_file']
        # current_dir = config['bot_config']['current_dir']
        # enabled_cmd = config['cmds_config']['enabled_cmd']
        # broadcast_unkown_messages = config['cmds_config']['broadcast_unkown_messages']
        # buttons_rows_per_page = int(config['cmds_config']['buttons_rows_per_page'])
        
        autoping = config['autoping']
        for server in autoping:
            logging.debug(autoping[server])
    else:
        if len(sys.argv) < 3:
            print('Usage: python run_bot.py TOKEN handle')
            exit()
        token = sys.argv[1]
        handle = sys.argv[2]
        db_file = 'botbase.db'
        current_dir = "."
        enabled_cmd = 'explore,help,ip,webip,logo,whoami,chatid,img,exec,execa,get,down,broadcast,print,sql,store,value,values'
        buttons_rows_per_page = 10
        logging.info('All commands are enabled, to disable them use a bot.properties file')
        
        config = configparser.ConfigParser()
        config['bot_config'] = {}
        config['bot_config']['token'] = bot_config.api_token
        with open(bot_properties_file, 'w+') as configfile:
            config.write(configfile)

except Exception as e:
    logging.error(str(e))

current_dir = script_path 

def add_autoping(new_monitored_host: str, new_monitored_host_label: str = None):
    try:
        config = configparser.ConfigParser()   
        autoping = {}   
        
        if new_monitored_host_label is None:
            new_monitored_host_label = new_monitored_host     
        
        try:
            config.read(bot_properties_file)
            autoping = config['autoping']
            
        except Exception as e:
            logging.error(str(e)) 
            config['autoping'] = {}      
        
        autoping[new_monitored_host_label] = new_monitored_host
        config['autoping'][new_monitored_host_label] = new_monitored_host
            
        with open(bot_properties_file, 'w+') as configfile:
            config.write(configfile)       
        
    except Exception as e:
        logging.error(str(e))

def add_org_name(new_organization: str):
        
    try:     
        config = configparser.ConfigParser()
        config['bot_config'] = {}
        config['bot_config']['organization'] = new_organization
        with open(bot_properties_file, 'w+') as configfile:
            config.write(configfile)      
        
    except Exception as e:
        logging.error(str(e))
    
    return org_name

def add_setting(section_name:str, setting_name: str, setting_value: str):
    try:
        config = configparser.ConfigParser()   
        new_setting = {}      
        
        try:
            config.read(bot_properties_file)
            new_setting = config[section_name]
            
        except Exception as e:
            logging.error(str(e)) 
            config[section_name] = {}      
        
        new_setting[setting_name] = setting_value
        config[section_name][setting_name] = setting_value
            
        with open(bot_properties_file, 'w+') as configfile:
            config.write(configfile)       
        
    except Exception as e:
        logging.error(str(e))

def del_autoping(new_monitored_host: str):
    try:
        config = configparser.ConfigParser()   
        autoping = {}        
        
        try:
            config.read(bot_properties_file)
            autoping = config['autoping']
            
        except Exception as e:
            logging.error(str(e)) 
            config['autoping'] = {}      
        
        #del autoping[new_monitored_host]
        del config['autoping'][new_monitored_host] 
            
        with open(bot_properties_file, 'w+') as configfile:
            config.write(configfile)       
        
    except Exception as e:
        logging.error(str(e))

def get_section(setting_name:str, bot_properties_file:str=bot_properties_file):
 
    setting_value = None # {}      
    
    try:
        config = configparser.ConfigParser()    
        
        try:
            config.read(bot_properties_file)
            setting_value = config[setting_name]
            
        except Exception as e:
            logging.error(str(e))         
        
    except Exception as e:
        logging.error(str(e))
    
    return setting_value

def get_setting(section_name:str, setting_name:str, bot_properties_file:str= globals()['bot_properties_file']):
 
    setting_value = None       
    
    try:
        config = configparser.ConfigParser()    
        
        try:
            config.read(bot_properties_file)
            setting_value = config[section_name][setting_name]
            
        except Exception as e:
            logging.error(str(e))         
        
    except Exception as e:
        logging.error(str(e))
    
    return setting_value

def get_autoping():
 
    autoping = {}      
    
    try:
        config = configparser.ConfigParser()    
        
        try:
            config.read(bot_properties_file)
            autoping = config['autoping']
            
        except Exception as e:
            logging.error(str(e))         
        
    except Exception as e:
        logging.error(str(e))
    
    return autoping

def get_org_name():
 
    org_name = ''      
    
    try:
        config = configparser.ConfigParser()
        config.read(bot_properties_file)
        org_name = config['bot_config']['organization']        
        
    except Exception as e:
        logging.error(str(e))
    
    return org_name

def get_stripe_token():
 
    stripe_token = {}      
    
    try:
        config = configparser.ConfigParser()    
        
        try:
            config.read(bot_properties_file)
            stripe_token = config['stripe_token']
            
        except Exception as e:
            logging.error(str(e))         
        
    except Exception as e:
        logging.error(str(e))
    
    return stripe_token

def main():
    
    autoping = get_section('autoping')
    for host in autoping:
        logging.debug(host)

    autoping = get_autoping()
    
    for host in autoping:
        logging.debug(f'{host} {autoping[host]}')
    
    add_autoping('teste.com.br')
    
if __name__ == '__main__':
	main() 
