#!/usr/bin/env python3.7

"""
Integração capiwha
"""

import sys

base_url = "panel.capiwha.com"
api_key = ''

import http.client
import logging
import urllib
import json

# Enable logging
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

def send_msg(phone_dest:str, message_to_send:str, api_key:str):
    data_decoded =  None
    http_response = None
    response_data_object = None
    
    try:
        conn = http.client.HTTPSConnection(base_url)

        raw_parameters = { 'text' : message_to_send}
        parameters = urllib.parse.urlencode(raw_parameters)
        
        request_url = f"/send_message.php?apikey={api_key}&number={phone_dest}&{parameters}"
        conn.request("GET", request_url)    

        http_response = conn.getresponse()
        logging.debug(f'{http_response.code} {http_response.reason}')  
        
        if http_response and (http_response.code == 200):   
            data_bytes_read = http_response.read()
            
            # message queued
            data_decoded = data_bytes_read.decode("utf-8")
            logging.debug(data_decoded)
            
            response_data_object = json.loads(data_decoded)
            logging.debug(f"{response_data_object['success']} : {response_data_object['description']} : {response_data_object['result_code']}")  
            
        else:
            logging.debug(f'Erro {http_response.code}')
            data_decoded = f'Erro {http_response.code}'
    
    except Exception as e:
        logging.error(str(e))
        data_decoded = str(e)
    
    return data_decoded, http_response, response_data_object    

def get_msg(phone_dest:str, api_key:str, type:str='IN', markaspulled:str='1', getnotpulledonly:str='1'):
    
    try:
        
        raw_parameters = { 'type' : type, 'markaspulled': markaspulled, 'getnotpulledonly': getnotpulledonly}
        parameters = urllib.parse.urlencode(raw_parameters)
                
        conn = http.client.HTTPSConnection(base_url)  
        request_url = f"/get_messages.php?apikey={api_key}&number={phone_dest}&{parameters}"
        conn.request("GET", request_url)    

        http_response = conn.getresponse()
        logging.debug(f'{http_response.code} {http_response.reason}')  
        
        if http_response and (http_response.code == 200):   
            data_bytes_read = http_response.read()
            
            # message queued
            data_decoded = data_bytes_read.decode("utf-8")
            logging.debug(data_decoded)
            
            response_data_object = json.loads(data_decoded)
            for response_data_item in response_data_object:
                logging.debug(f"{response_data_item['number']} : {response_data_item['from']} : {response_data_item['type']}  {response_data_item['text']}")  
            
        else:
            logging.debug(f'Erro {http_response.code}')
            data_decoded = f'Erro {http_response.code}'                  
    
    except Exception as e:
        logging.error(str(e))
        data_decoded = str(e)    

    return data_decoded, http_response, response_data_object

# ------ Teste unitário -------

def unit_test():
    """Teste unitário."""

    try:
        
        global api_key 
        if len(sys.argv) > 1:
            api_key = sys.argv[1] 
        else:
            api_key = input("Api key: ")
            
        phone_dest = ''    
        if len(sys.argv) > 2:
            phone_dest = sys.argv[2] 
        else:
            phone_dest = input("Destinatário da mensagem de teste: ")
        
        data_decoded, http_response, response_data_object = send_msg(phone_dest, 'message test', api_key)
        logging.info(data_decoded)			
        
        if http_response and data_decoded and response_data_object:
            logging.debug(f"{response_data_object['success']} : {response_data_object['description']} : {response_data_object['result_code']}")  
        elif http_response:
            logging.error(f'{http_response.code} {http_response.reason}')      
        else:
            logging.error('Erro')
    
        get_msg(phone_dest=phone_dest, api_key=api_key) 
        
    except Exception as e:
        logging.error(str(e))      

if __name__ == '__main__':
    unit_test() 
