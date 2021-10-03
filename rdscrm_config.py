#!/usr/bin/env python3.7

# pip install pysqlite3 

import logging

import sys
import socket
import telegram

import os

# set up logging to standard output
logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s","%(name)s","%(levelname)s","%(message)s') 

# Tlg API Token
api_token 		= "" 	  
dev_api_token 	= "Coloque aqui o token da API Telegram (ambiente de desenvolvimento)"  	
prod_api_token 	= "Coloque aqui o token da API Telegram (ambiente de produção)" 		

# Caso esteja rodando em ambiente de produção, utiliza token de produção
if os.environ.get('ENVIRONMENT') == 'dev':
	api_token = dev_api_token
else:
	api_token = prod_api_token 

# Id do administrador principal do Bot (dono do Bot)
admin_telegram_id = 138429124 # Coloque aqui o seu ID do Telegram

# Grupo de administradores
admin_group = [
	# coloque aqui separados por vírgulas outros usuários administradores do Bot, 
 	# que poderão usar os comandos aadministrativos
	12345678, 98765432
]

# Nome do script que está rodando
script_name = sys.argv[0]

# Nome da máquina 
host_name = socket.gethostname().upper()

# Link de suporte
default_suppport_link = f'https://t.me/rdstationcrm' 

# Texto de ajuda
help_text = f"_Comandos disponíveis:_\
    \n*/token* _Exibir ou alterar token RDStation CRM - Novo token opcional_\
    \n*/usu* _Listar usários - Filtro opcional _\
    \n*/oport* _Listar oportunidades - Filtro opcional _\
    \n*/tarefas* _Listar tarefas - Filtro opcional_\
    \n*/anota* _Listar anotações - Filtro opcional_\
    \n*/filtro* _Liga/desliga listagem por usuário - liga/desliga_\
	\n*/start* _entrar 🚪_\
	\n*/help* _ajuda_\
	\n*Acesse o grupo:*\
	\n{default_suppport_link}"
 
help_text_admin = f"_Comandos disponíveis:_\
    \n*/token* _Exibir ou alterar token RDStation CRM - Novo token opcional_\
    \n*/usu* _Listar usários - Filtro opcional _\
    \n*/oport* _Listar oportunidades - Filtro opcional _\
    \n*/tarefas* _Listar tarefas - Filtro opcional_\
    \n*/tconfig* _Liga/desliga listagem tarefas não concluídas - liga/desliga_\
    \n*/filtro* _Liga/desliga listagem por usuário - liga/desliga_\
    \n*/anota* _Listar anotações - Filtro opcional_\
	\n*/restart* _Reiniciar o Bot _\
	\n*/stop* _Parar o Bot _\
	\n*/admin* _Gerenciar administradores _\
	\n*/ver* _Exibir versão e dados do Bot_\
	\n*/pag* _Alterar paginação de listagens - [página atual] [tamanho-pagina]_\
	\n*/pag* _Alterar paginação - pagina inicial - tamanho pagina_\
	\n*/start* _entrar 🚪_\
	\n*/help* _ajuda_\
	\n*Acesse o grupo:*\
	\n{default_suppport_link}"

start_message = "* 👋 Bem-vindo ao * *%s*_!_" # %str(bot_client.username)

# Configurações globais de paginação de listagens
page_start = 1 		# página inicial a ser exibida
page_size = 20		# quantidade de linhas por página

# Configurações de listagem de tarefas
done_filter = "false"

# Configuração de filtro listagens em geral por usuário
filter_by_user = True # False

"""
Comandos:
token - Associar token do RDStation CRM ao Bot 
tarefas - <filtro opcional> - Listar tarefas
anota - <filtro opcional> - Listar anotações
start - Começar
help - Ajuda
"""