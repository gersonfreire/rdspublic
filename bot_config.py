#!/usr/bin/env python3.7

import logging

import sys
import socket
import telegram

version = """
7.8.1 - Ativa ou desativa interface de botões com menus 
"""

import os

# set up logging to standard output
logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s","%(name)s","%(levelname)s","%(message)s') 

# Tlg API Token
api_token 		= "" 	
admin_api_token = "" 	
dev_api_token 	= ""  	
prod_api_token 	= "" 	

# Caso esteja rodando em ambiente de produção, define token de produção
if os.environ.get('ENVIRONMENT') == 'dev':
	api_token = dev_api_token
else:
	api_token = prod_api_token 

# paypal rfbot app  
paypal_client_id = "" # "<<PAYPAL-CLIENT-ID>>"
paypal_client_secret = "" # "<<PAYPAL-CLIENT-SECRET>>"

# Usuário do servidor SQL
users_dic = {}

# Id do administrador e do grupo de administradores
admin_telegram_id = 138429124
admin_group = []

# Conexão API Tlg
bot_client:telegram.Bot = None

# Nome do script que está rodando
script_name = sys.argv[0]

# Nome da máquina 
host_name = socket.gethostname().upper()

# Máquina de produção default
default_prod_host_name = ''

# Link de suporte
default_suppport_link = f'' 

# Texto de ajuda
# https://gist.github.com/naiieandrade/b7166fc879627a1295e1b67b98672770
# Unicode emojis for Telegram
help_text = f"_Comandos disponíveis:_\
	\n*/start* _entrar 🚪_\
	\n*/help* _ajuda_\
	\n*Acesse o grupo:*\
	\n%s"

help_link = "\n\nPara maiores detalhes: \n"
help_link_admin = "\n\nPara maiores detalhes: \n"

help_text_admin = """
/admin - lista usuários administradores 🚀
/alarm - código do controlador - lista alarmes em TEMPO REAL dado o código do controlador
/autobot - servidor email senha - cria e executa novo bot ✔️
/aviso - mensagem - envia mensagem para todos os usuarios
/autoping - endereço do computador - monitora por ping um servidor ⚠️
/autoriza - número usuário - autoriza usuário a receber alarmes
/autorizados - ver somente os usuários autorizados
/baixar - não precisa digitar comando, apenas clique no Clipe de envio de arquivos do Telegram
/bkp - download do arquivo de armazenamento de usuários
/codigo - texto - insere código do Google para ativar conexão à API do Gmail 
/config - verconfiguração de leitura de e-mails 🛠
/contato - telefone com ddd - adiciona um contato para receber alarme de voz
/contatosms- telefone com ddd - adiciona ou remove um telefone para receber alarme por SMS
/contatozap - telefone com ddd - adiciona um contato para receber alarme de zap
/controladores - código do conversor - lista controladores por conversor 
/conversores - lista todos os conversores conectados num servidor SITRAD
/dbconfig - configuração - ver ou alterar configuração de conexão ao servidor remoto
/dbtest - testa acesso ao servidor de banco de dados remoto
/google - mostra link de autorização para conexão segura ao Gmail
/help - ajuda
/interval - tempo em segundos - intervalo para leitura de e-mails
/imap - liga/desliga - monitoramento de email
/imaplog - liga / desliga - log de depuração de alarmes
/imaptest - testa conexão ao servidor de e-mails
/liberatodos - liga ou desliga - liga ou desliga bloqueio de usuários não autorizados
/link - altera link de suporte
/listabots - mostra Bots em execução no servidor de Bots
/log - visualiza histórico de erros de envio de mensagens
/novobot - token - servidor_email - usuario - senha - cria novo bot
/paghist - lista historico de transações recentes
/ping - endereço - testa conexão ao servidor remoto 
/restart - reinicia o bot
/saldo - saldo atual do usuário
/servidor - liga/desliga - liga ou desliga conexão ao banco de dados do servidor ✅
/sms - liga/desliga - liga ou desliga envio de alarmes por SMS
/smsenvia - mensagem - envia mensagem para todos os usuários cadastrados
/smsenvia1 - [telefone] mensagem - envia mensagem para o usuario especifico do [telefone]
/smslist - lista contatos que recebem SMS
/sondas - código - exibe temperaturas em tempo real, dado o código  do controlador
/sitradlist - lista servidores SITRAD conectados
/sitradserver - codigo-servidor - exibe ou altera o servidor SITRAD atual 
/start - entrar no bot
/stop - parar bot
/testgmail - verifica conexão à API do Gmail
/tokens - lista, acrescenta e apaga bots
/usuarios - ver todos os usuários autorizados ou não
/usegmail - liga/desliga - modo de leitura do Gmail (API/IMAP)
/ver - versão do bot
/voz - liga / desliga - liga ou desliga alarme por voz ☎️ 
/vozlist - lista usuários de alarme de voz ☎️
/zaplist - lista usuários de alarme de zap ☎️
"""

from telegram.bot import Bot, BotCommand
bot_commands = [
	#BotCommand("start","Começar"),
	#BotCommand("help", "Ajuda")
	BotCommand("admin","lista usuários administradores 🚀"),
	BotCommand("alarm","código do controlador - lista alarmes em TEMPO REAL dado o código do controlador"),
	BotCommand("autobot","servidor email senha - cria e executa novo bot ✔️"),
	BotCommand("autoping","endereço do computador - monitora por ping um servidor ⚠️"),
	BotCommand("autoriza","número usuário - autoriza usuário a receber alarmes"),
	BotCommand("autorizados","ver somente os usuários autorizados"),
	BotCommand("baixar","Para enviar arquivo, não precisa digitar comando, apenas clique no Clipe de envio de arquivos do Telegram"),
	BotCommand("bkp","download do arquivo de armazenamento de usuários"),
	BotCommand("codigo","texto - insere código do Google para ativar conexão à API do Gmail"),
	BotCommand("config","verconfiguração de leitura de e-mails 🛠"),
	BotCommand("contato","telefone com ddd - adiciona um contato para receber alarme de voz"),
	BotCommand("contatozap","telefone com ddd - adiciona um contato para receber alarme de zap"),
	BotCommand("controladores","código do conversor - lista controladores por conversor"),
	BotCommand("conversores","lista todos os conversores conectados num servidor SITRAD"),
	BotCommand("dbconfig","configuração - ver ou alterar configuração de conexão ao servidor remoto"),
	BotCommand("dbtest","testa acesso ao servidor de banco de dados remoto"),
	BotCommand("google","mostra link de autorização para conexão segura ao Gmail"),
	BotCommand("help","ajuda"),
	BotCommand("interval","tempo em segundos - intervalo para leitura de e-mails"),
	BotCommand("imap","liga/desliga - monitoramento de email"),
	BotCommand("imaplog","liga / desliga - log de depuração de alarmes"),
	BotCommand("imaptest","testa conexão ao servidor de e-mails"),
	BotCommand("liberatodos","liga ou desliga - liga ou desliga bloqueio de usuários não autorizados"),
	BotCommand("link","altera link de suporte"),
	BotCommand("listabots","mostra Bots em execução no servidor de Bots"),
	BotCommand("log","visualiza histórico de erros de envio de mensagens"),
	BotCommand("novobot","token - servidor_email - usuario - senha - cria novo bot"),
	BotCommand("ping","endereço - testa conexão ao servidor remoto"),
	BotCommand("restart","reinicia o bot"),
	BotCommand("servidor","liga/desliga - liga ou desliga conexão ao banco de dados do servidor ✅"),
	BotCommand("sondas","código - exibe temperaturas em tempo real, dado o código  do controlador"),
	BotCommand("sitradlist","lista servidores SITRAD conectados"),
	BotCommand("sitradserver","codigo-servidor - exibe ou altera o servidor SITRAD atual"),
	BotCommand("start","entrar no bot"),
	BotCommand("stop","parar bot"),
	BotCommand("testgmail","verifica conexão à API do Gmail"),
	BotCommand("tokens","lista, acrescenta e apaga bots"),
	BotCommand("usuarios","ver todos os usuários autorizados ou não"),
	BotCommand("usegmail","liga/desliga - modo de leitura do Gmail (API/IMAP)"),
	BotCommand("ver","versão do bot"),
	BotCommand("voz","liga / desliga - liga ou desliga alarme por voz ☎️"),
	BotCommand("vozlist","lista usuários de alarme de voz ☎️"),
	BotCommand("zaplist","lista usuários de alarme de zap ☎️")
]


support_text = f"Comando não existente:\n%s.\
			\nAcesse o grupo:\
			\n%s"

# Caracteres especiais ASCII
# https://fsymbols.com/font
# start_message = "* 👋 ℬℯ𝓂-𝓋𝒾𝓃𝒹ℴ 𝒶ℴ * *%s*_!_" # %str(bot_client.username)
start_message = "* 👋 Bem-vindo ao * *%s*_!_" # %str(bot_client.username)

# Tempo default entre agendamentos
DEFAULT_POOLING_SECONDS = 60 # a cada 1 minuto

# ----------- Configurações de segurança do Bot

# Permite novos usuários receberem alarmes sem autorização prévia
AUTO_ALLOW_NEW_USERS = False

# ----------- Configurações específicas

# Alarme de voz ligado/desligado
VOICE_STATUS = False

# Alarme via zap ligado/desligado
ZAP_STATUS = False

# Alarme via SMS ligado/desligado
SMS_STATUS = False

# Filtro de assunto de monitoramento de email
# default_subject_filter = 'Alarmes SmartMonit' # assunto padrão
default_subject_filter = None 

# Filtro de linhas de alarme a serem omitidas
default_remove_alarm_line = 'Finalizado'
default_filters_list = ['Finalizado'] #, 'Falha de comunicação']

# Filtro de exibição apenas para destinatários específicos
show_only_for_user = {
}

# integração com servidor de Bots ativa
is_bot_manager_active = True

# log de e-mails ativo
is_bot_remote_log_active = True

# Configuração de IMAP é exclusiva para este Bot?
is_imap_owner = True

# Ativa/Desativa monitoramento de e-mails
is_imap_monitor_active = True

# Ativa/desativa log de leitura de e-mails no bot
is_imap_log_bot_active = True

# Usar GMAIL API para leitura de emails do Gmail
use_gmail_api = False

# Monitoramento de computadores, inicia com o próprio host local
host_monitored = socket.gethostname().upper()
host_monitored_list = \
[
    'localhost'
]

# comando usado para lista Bots em execução exceto pelo VS Code
bots_list_command_line = 'pgrep -a python|grep "\.\/"|cut -d" " -f 3' 

# libera bot para reutilização por outro usuário ou não
is_reusable_bot = True

# Cria e-mail TrackFreeze automatico
auto_create_email = True

def set_config():
	result = False

	global admin_telegram_id
	try:
		if util_sql_autobot.set_config(globals()):  
			admin_telegram_id = int(admin_telegram_id)
			result = True
  
	except Exception as e:
		logging.error(str(e)) 

	return result

# força a leitura dos emails com layout padrão Sitrad
is_sitrad_layout=True

# API Key do provedor ApiWHA
wha_api_key = ''

# Contatos para envio de zap
zap_contacts = [
]

# Contatos para envio de SMS
sms_contacts = [
]

# 7.8.0 Ativa ou desativa interface de botões com menus 
is_menu_enabled = True

# ---------- Testes unitarios -----------

def main():
  
	try:
		set_config()
	except Exception as e:
		logging.error(str(e)) 	

if __name__ == '__main__':
    main() 
