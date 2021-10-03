#!/usr/bin/env python3.7

"""
Integração com RDStation CRM
https://crmsupport.rdstation.com.br/hc/pt-br/articles/360018747911-Integra%C3%A7%C3%B5es-via-API-com-outras-plataformas
"""

import sys
import os

import json
import requests

import logging

import db.util_db_users as db_users

logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
 
_base_url = 'https://plugcrm.net/api/v1'
_user_token = ""

#----------
# Consome métodos genéricos API
def api_client(
    route:str, method_type = 'GET',
    payload:str = None,
    user_token:str = None, base_url:str = None,
    page_number:int = 1, page_size:int = 20
    ):

    response = None

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None :
            user_token = _user_token

        if is_token_valid(user_token):
            url = f"{base_url}/{route}"

            # https://plugcrm.net/api/v1/contacts?token=MyToken&page=Page&limit=Limit&q=Query
            if payload is None:
                payload = json.dumps({
                    "token": f"{user_token}",
                    "page": f'{page_number}',
                    "limit": f'{page_size}'
                })

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.request(method_type, url, headers=headers, data=payload)

    except Exception as e:
        logging.error(str(e))

    return response
 
# ------------------------------------------
# ---------------- Usuários https://plugcrm.net/api/v1/contacts/IdContato?token=MyToken   
# ------------------------------------------
def get_users_api(
    user_token:str = None, base_url:str = None
    ):

    response = None

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None :
            user_token = _user_token

        if is_token_valid(_user_token):
            url = f"{base_url}/contacts"

            payload = json.dumps({
                "token": f"{user_token}"
            })

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.request("GET", url, headers=headers, data=payload)

    except Exception as e:
        logging.error(str(e))

    return response

def get_contacts(
    contact_id:str = None,
    user_token:str = None, base_url:str = None,
    page_number:int = 1, page_size:int = 20
    ):

    response_list = {}
    total = 0
    has_more = False

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None :
            user_token = _user_token
                    
        # GET https://plugcrm.net/api/v1/contacts?token=MyToken&page=Page&limit=Limit&q=Query
        # GET https://plugcrm.net/api/v1/contacts/IdContato?token=MyToken  
        contact_id = f'/{contact_id}' if contact_id else ''     
        response = api_client(
            f"contacts{contact_id}", 
            page_number=page_number, page_size=page_size,
            user_token=user_token
            )
        
        logging.debug(response) 
        if response.ok:
            response_object = json.loads(response.text)    
            logging.debug(response_object)
            
            # Se retornou lista de contatos
            if not contact_id:
                total = response_object['total']
                has_more = response_object['has_more']
                for response_item in response_object['contacts']:
                    logging.debug(response_item)     
                    response_list[response_item['id']] = response_item
            else:
                response_list = response_object

    except Exception as e:
        logging.error(str(e))

    return response_list, total, has_more

def get_user_by_phone(phone:str, user_list:dict = None):
    
    try:
        if user_list is None:
            user_list, total, has_more = get_contacts()
        
        for user_item in user_list:
            phones_list = user_list[user_item]['phones']
            for phone_item in phones_list:
                if phone_item['phone'] == phone:
                    return user_list[user_item]
                
    except Exception as e:
        logging.error(str(e))

# Verifica se ID do usuário existe no Telegram
def get_user_by_tlg_id(chat_id:str, user_list:dict = None):
    
    try:
        custom_field_id = ''
        custom_field = get_custom_field_by_label('Contato Telegram')
        if not custom_field is None:
            custom_field_id = custom_field['_id']
            
            # user_list[user_item]['contact_custom_fields'][0]['value']
                
            if user_list is None:
                user_list, total, has_more = get_contacts()
                
            for user_item in user_list:
                if len(user_list[user_item]['contact_custom_fields']) > 0:
                    for custom_field in user_list[user_item]['contact_custom_fields']:
                        if custom_field['custom_field_id'] == custom_field_id:
                            if custom_field['value'] == str(chat_id):
                                return user_list[user_item]
        
    except Exception as e:
        logging.error(str(e))

# adicionar usuário do Chat ao RD
def add_rd_user(
    contact_name:str, organization_id:str = None, 
    contact_title:str = None,
    organization_url:str = None,
    contact_email:str = None,
    contact_phone:str = None,
    birth_day:int = 0, birth_month:int = 0, birth_year = 0,
    chat_id:str = None,
    custom_field_id:str = None,
    chat_custom_field_id:str = None,
    user_token:str = None):
    
    try:
        
        if user_token is None :
            user_token = _user_token

        token_obj = {
            "token": user_token,
        }
        
        emails = [
            {
                "email": contact_email 
            }
        ]

        phones = [
            {
                "phone": contact_phone 
            }
        ]
        
        deal_ids = [
            None
        ]
        
        legal_bases = [
            {
                "category": "data_processing",
                "type": "consent",
                "status": "granted"
            },
            {
                "category": "communications",
                "type": "vital_interest",
                "status": "granted"
            }
        ]         
        
        birthday =  {
            "day": birth_day, 
            "month": birth_month , 
            "year": birth_year
        }           
        
        # Contato Telegram
        contact_custom_fields = [
            {
                '_id': custom_field_id, # '614894fb053b7e0020f3b00b', 
                'created_at': None, 
                'custom_field_id': chat_custom_field_id, #'5ec6d14cf02baf002e208aee', 
                'updated_at': None, 
                'value': chat_id 
            }
        ] 
                      
        
        contact_obj = {
            "contact": {
                "name": contact_name,
                "organization_id": organization_id if organization_id else '0', 
                "title": contact_title,
                "birthday": birthday if birth_day > 0 else None,
                "url": organization_url,  
                "emails": emails if contact_email else None,
                "phones": phones if contact_phone else None,
                "deal_ids": deal_ids,
                "legal_bases": legal_bases,
                "contact_custom_fields" : contact_custom_fields
            }           
        }      
        
        # https://stackoverflow.com/questions/1781571/how-to-concatenate-two-dictionaries-to-create-a-new-one-in-python
        # Concatena dois dicionarios
        json_obj = dict(token_obj, **contact_obj)
        
        # Estrutura em JSON da requisição de POST para criar Contato:
        {
            "token": "MY_TOKEN",
            "contact": {
                "name": "nomedocontato",
                "title": "titulodocontato",

                "birthday": {"day": 11, "month": 9, "year": 1979},

                "emails": [
                    {
                        "email": "fulano@email.com.br"
                    }
                ],
                
                "phones": [
                    {
                        "phone": "71304556"
                    }
                ],
                
                "organization_id": "ID_EMPRESA",
                "deal_ids": [
                    "ID_OPORTUNIDADE1",
                    "ID_OPORTUNIDADE2"
                ],
                
                "legal_bases": [
                    {
                        "category": "data_processing",
                        "type": "consent",
                        "status": "granted"
                    },
                    {
                        "category": "communications",
                        "type": "vital_interest",
                        "status": "granted"
                    }
                ]
            }
        }            
        
        payload = json.dumps(json_obj) 
        
        # POST https://plugcrm.net/api/v1/contacts
        response = api_client("contacts", "POST", payload=payload)
        
        logging.debug(response)
        
        if response.ok:
            return json.loads(response.text)         
    
    except Exception as e:
        logging.error(str(e))    

# Atualiza contato RD - PUT https://plugcrm.net/api/v1/contacts/iddocontato
def upd_contact_by_id(
    contact_id:str,
    contact_name:str = None, organization_id:str = None, 
    contact_title:str = None,
    organization_url:str = None,
    contact_email:str = None,
    contact_phone:str = None,
    birth_day:int = 0, birth_month:int = 0, birth_year = 0,
    chat_id:str = None,
    custom_field_id:str = None,
    chat_custom_field_id:str = None,
    user_token:str = None):
  
    try:
        
        if user_token is None :
            user_token = _user_token

        token_obj = {
            "token": user_token,
        }
        
        emails = [
            {
                "email": contact_email 
            }
        ]

        phones = [
            {
                "phone": contact_phone 
            }
        ]
        
        deal_ids = [
            None
        ]
        
        legal_bases = [
            {
                "category": "data_processing",
                "type": "consent",
                "status": "granted"
            },
            {
                "category": "communications",
                "type": "vital_interest",
                "status": "granted"
            }
        ]         
        
        birthday =  {
            "day": birth_day, 
            "month": birth_month , 
            "year": birth_year
        }           
        
        # Contato Telegram
        contact_custom_fields = [
            {
                '_id': '614894fb053b7e0020f3b00b', # custom_field_id, # '614894fb053b7e0020f3b00b', 
                'created_at': None, # {"day": 11, "month": 9, "year": 1979},
                'custom_field_id': '5ec6d14cf02baf002e208aee', # chat_custom_field_id, #'5ec6d14cf02baf002e208aee', 
                'updated_at':  None, # {"day": 11, "month": 9, "year": 1979},
                'value': chat_id if chat_id else ''
            }
        ] 
                      
        
        contact_obj = {
            "contact": {
                "name": contact_name,
                "organization_id": organization_id if organization_id else '0', 
                "title": contact_title,
                "birthday": birthday if birth_day > 0 else None,
                "url": organization_url,  
                "emails": emails if contact_email else None,
                "phones": phones if contact_phone else None,
                "deal_ids": deal_ids,
                "legal_bases": legal_bases,
                "contact_custom_fields" : contact_custom_fields
            }           
        }      
        
        # https://stackoverflow.com/questions/1781571/how-to-concatenate-two-dictionaries-to-create-a-new-one-in-python
        # Concatena dois dicionarios
        json_obj = dict(token_obj, **contact_obj)                 
        
        payload = json.dumps(json_obj) 
        
        # PUT https://plugcrm.net/api/v1/contacts/iddocontato
        response = api_client(f"contacts/{contact_id}", "PUT", payload=payload)
        
        logging.debug(response)
        
        if response.ok:
            return json.loads(response.text)             
    
    except Exception as e:
        logging.error(str(e))      
 
# ------------------------------------------
# ---------------- Token https://plugcrm.net/api/v1/token/check     
# ------------------------------------------
def get_token(
    user_token:str = None, base_url:str = None
    ):

    response = None

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        url = f"{base_url}/token/check"

        payload = json.dumps({
            "token": f"{user_token}"
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

    except Exception as e:
        logging.error(str(e))

    return response

def is_token_valid(user_token:str = None, base_url:str = None)->bool:
    
    result = False

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token
            
        if (user_token != '') and (not user_token is None):

            tasks_response = get_token(
                base_url=base_url, user_token=user_token
                )

            if tasks_response.ok:
                response_object = json.loads(tasks_response.text)
                response_field_value = response_object['name']
                result = True

    except Exception as e:
        logging.error(str(e))

    return result

# ------------------------------------------
# ---------------- Campos personalizados 
# ------------------------------------------

# Listar : https://plugcrm.net/api/v1/custom_fields?token=MyToken
def get_custom_fields(token:str = None):
    result = {}
    
    try:
        response = api_client("custom_fields")
        
        logging.debug(response) 
        if response.ok:
            response_object = json.loads(response.text)    
            logging.debug(response_object)
            for response_item in response_object['custom_fields']:
                logging.debug(response_item) 
                result[response_item['_id']] = response_item    
                        
    except Exception as e:
        logging.error(str(e))    
    
    return result

def get_custom_field_by_label(label:str, token:str = None, field_list:dict = None):
    
    try:
       if field_list is None:
           field_list = get_custom_fields()
           for field_item in field_list:
                if str(field_list[field_item]['label']).lower() == label.lower():
                    return field_list[field_item]
                    
    except Exception as e:
        logging.error(str(e))

def get_users_all():
    try:
        # obter lista de todos os contatos do RDStation
        page_size = 100
        all_users, total, has_more = get_contacts(page_size=page_size) 
        if has_more:
            page_number = 2
            total_pages = int(total / page_size) + ((total % page_size) > 0)
            for next_page in range(page_number, total_pages + 1, 1):
                user_list, total, has_more = get_contacts(page_number=next_page, page_size=page_size) 
                
                # https://stackoverflow.com/questions/1781571/how-to-concatenate-two-dictionaries-to-create-a-new-one-in-python
                # Concatena dois dicionarios
                # all_users = all_users + user_list
                # $ python -mtimeit -s'd1={1:2,3:4}; d2={5:6,7:9}; d3={10:8,13:22}' \
                # 'd4 = dict(d1, **d2); d4.update(d3)' 
                all_users = dict(all_users, **user_list) # ; all_users2.update
                
        return all_users
                           
    except Exception as e:
        logging.error(str(e))   

# Sincroniza usuários RD a partir do Bot
def sync_rd_from_db(
    all_rd_users:dict = None,
    all_bot_users:dict = None,
    custom_field_id:str = None,
    chat_custom_field_id:str = None,
    user_token:str = None    
):

    try: 
        if user_token is None :
            user_token = _user_token
                       
        if not all_rd_users:
            # obter lista de todos os contatos do RDStation
            all_rd_users = get_users_all()
                
        if not all_bot_users:
            # Obter lista de todos os usuários do bot
            all_bot_users = db_users.get_all()
            
        # Para cada usuário do Bot, tenta associar 
        each_user:db_users.User
        rd_user = None
        for each_user in all_bot_users:
            logging.debug(each_user.user_name)
            
            if each_user.chat_id:
                
                rd_user = get_user_by_tlg_id(str(each_user.chat_id), user_list=all_rd_users)
                
                # Se contato já existir no RD, atualiza
                if rd_user:
                    # Atualiza ID RD no bot
                    each_user.rdstation_id = rd_user['id']
                    # Salva alterações no b.d.
                    db_users.session.commit()  
                                        
                    updated_user = upd_contact_by_id(
                        contact_id=rd_user['id']
                        ,contact_name=rd_user['name']
                        ,organization_id=rd_user['organization_id']
                        ,chat_id=str(each_user.chat_id),
                        custom_field_id= custom_field_id, 
                        chat_custom_field_id = chat_custom_field_id)
                    
                # Se não encontrar pelo ID no RD, tenta encontrar pelo telefone
                else:
                    rd_user = get_user_by_phone(str(each_user.phone), user_list=all_rd_users)                 
                    if rd_user:
                        updated_user = upd_contact_by_id(
                            contact_id=rd_user['id']
                            ,contact_name=rd_user['name']
                            ,organization_id=rd_user['organization_id']
                            ,contact_phone=str(each_user.phone)
                            ,chat_id=str(each_user.chat_id),
                            custom_field_id= custom_field_id, 
                            chat_custom_field_id = chat_custom_field_id) 
                    # Se não achou pelo telefone nem pelo ID, cria novo usuário                     
                    else:                          
                        new_user = add_rd_user(
                            contact_name= each_user.user_name, 
                            custom_field_id= custom_field_id, 
                            chat_custom_field_id = chat_custom_field_id,
                            chat_id=str(each_user.chat_id)) 
                        # Atualiza ID RD no bot e salva alterações no b.d.
                        each_user.rdstation_id = new_user['id']
                        db_users.session.commit()                                       
                             
    except Exception as e:
        logging.error(str(e))        
                
# ---------------------------
# Teste unitário
def unit_test():
    
    global _user_token    
    _user_token = sys.argv[3]  
    
    # Testa retorno de lista de contatos
    response_list, total, has_more = get_contacts()        
    
    # Obtem todos os contatos do RD
    all_rd_users = get_users_all()
    
    # Obtem todos os usuarios do Bot
    all_bot_users = db_users.get_all()
    
    # Sincroniza usuários RD a partir do Bot
    sync_rd_from_db(
        all_rd_users= all_rd_users,
        all_bot_users= all_bot_users,
        custom_field_id= '614894fb053b7e0020f3b00b', 
        chat_custom_field_id = '5ec6d14cf02baf002e208aee',        
    )                
    
    # Testa alteração de usuário pelo id do bot
    rd_user = get_user_by_tlg_id(str(913232747), user_list=all_rd_users)    
    if rd_user:    
        updated_user = upd_contact_by_id(
            contact_id=rd_user['id']
            ,contact_name=rd_user['name']
            ,organization_id=rd_user['organization_id']
            ,contact_title='CTO'
            ,chat_id=str(913232747)
            )
    else:
        new_user = add_rd_user('Teste @teste', 
            custom_field_id= '614894fb053b7e0020f3b00b', 
            chat_custom_field_id = '5ec6d14cf02baf002e208aee',
            chat_id=str(913232747))             
     
    # Testa alteração de usuário pelo telefone do bot
    rd_user = get_user_by_phone(str(67996080352), user_list=all_rd_users)    
    if rd_user:    
        updated_user = upd_contact_by_id(
            contact_id=rd_user['id']
            ,contact_name=rd_user['name']
            ,contact_phone=str(67996080352)
            ,organization_id=rd_user['organization_id']
            ,contact_title='CTO'
            ,chat_id=str(1384291214)
            )
    else:
        new_user = add_rd_user('Jonh Doe', 
            custom_field_id= '614894fb053b7e0020f3b00b', 
            chat_custom_field_id = '5ec6d14cf02baf002e208aee',
            chat_id=str(1384291214))             
        
    # TODO: Sincroniza usuários do Bot a partir do RD 
    
    custom_field = get_custom_field_by_label('Contato Telegram') 
    if not custom_field is None:
        custom_field_id = custom_field['_id']
        rd_user = get_user_by_tlg_id(sys.argv[1])
    
    response_list, total, has_more = get_contacts()
    
    logging.debug(response_list) 
    for response_item in response_list:
        logging.debug(response_item)
    
    user_by_phone = get_user_by_phone('71920012742')
    
    logging.debug(user_by_phone)
  

if __name__ == '__main__':
    unit_test() 
    
"https://plugcrm.net/api/v1/contacts"

"""
# https://stackoverflow.com/questions/1781571/how-to-concatenate-two-dictionaries-to-create-a-new-one-in-python
# Concatena dois dicionarios
json_obj = dict(token_obj, **contact_obj)

# d4 = dict(d1.items() + d2.items() + d3.items())
# d4 = dict(d1)
# d4.update(d2)            
# d4 = dict(d1, **dict(d2, **d3))  
"""

