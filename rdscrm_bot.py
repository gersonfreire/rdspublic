#!/usr/bin/env python3.7

"""
Integração com RDStation CRM
https://crmsupport.rdstation.com.br/hc/pt-br/articles/360018747911-Integra%C3%A7%C3%B5es-via-API-com-outras-plataformas
"""

# TODO: personalizar Welcome /start

# TODO: testar checkbox
# TODO: criar um método global para tratar novos usuários

# --- importa bibliotecas/dependências

import os
import sys
import signal

import re

import logging
from warnings import filters

import rdscrm_config as config

from telegram import Update, message, parsemode, user
import telegram
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

from telegram.ext.dispatcher import Dispatcher
from telegram.bot import BotCommand
    
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# executa comandos sistema operacional
import subprocess

from threading import Thread

import requests
import json

import sqlite3

import global_vars
import util_config

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f'{path}/util')
sys.path.append(f'{path}/util/db')
import util.util_rd_crm

import util.db.util_db_users as db_users

# -----------

# Testado com sucesso
version = "1.4.1" # mostra configuração de paginação

# Nome padrão do arquivo de configuração
config_default_file = 'config' 

# Bot users internal cache
users_cache = {}
all_bot_users = None

# Obtem token do argumento de linha de comando
if len(sys.argv) > 1:
    logging.info(f'API Token: {sys.argv[1]}')
    config.api_token = sys.argv[1]
    logging.debug(config.api_token)
else:
    config.api_token = input("Digite API token do Bot: ")   # Python 3

# Obtem ID do administrador da linha de comando
if len(sys.argv) > 2:
    logging.info(f'Admin: {sys.argv[2]}')
    config.admin_telegram_id = int(sys.argv[2])
    logging.debug(config.admin_telegram_id)
else:
    config.admin_telegram_id = input("Digite ID Telegram do Administrador: ")   # Python 3

try:
    updater = Updater(config.api_token, use_context=True)

    # mostra penas os comandos básicos
    bot_commands = [
        BotCommand("token", "Exibir ou alterar token RDStation CRM - <novo token opcional>"),
        BotCommand("usu","Listar usuários - <Filtro opcional>"),
        BotCommand("tarefas","Listar tarefas - <Filtro opcional>"),
        BotCommand("filtro","Liga/desliga listagens por usuário - liga/desliga"),
        BotCommand("tconfig","Liga/desliga listagem tarefas não concluídas - liga/desliga"),
        BotCommand("oport", "Listar oportunidades - <Filtro opcional>"),
        BotCommand("anota", "Listar anotações - <Filtro opcional>"),
        BotCommand("pag", "Listar anotações - <Filtro opcional>"),
        BotCommand("start", "Entrar"),
        BotCommand("help", "Ajuda")
        ]
    updater.bot.set_my_commands(bot_commands)
  
    config_default_file = f'config_{updater.bot.username}.db'
    
except Exception as e:
    logging.error(str(e))
    logging.error('API token do BOT inválido!')
    exit()

# ----- parametros de conexão

_user_token = ""
_users_tokens = {}
_current_rd_id = {}

# Dicionário de usuários RDStation por id Telegram
_rd_users_ = {}
_current_rd_user = None
 
_base_url = 'https://plugcrm.net/api/v1'

# ----- Tratamentos globais de comandos e mensagens

def global_handler(update: Update, context: CallbackContext) -> None:
    """Handle all messages"""

    global config_default_file
    global _rd_users_
    
    try:
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)
        
        _users_tokens[update.effective_chat.id] = get_rdstation_token(update.effective_chat.id, db_file=config_default_file)
                                    
        tlg_username = ('@' + update.effective_chat.username) if update.effective_chat.username else ''
        full_username = update.effective_chat.first_name + ' ' + \
            update.effective_chat.last_name + ' ' + str(tlg_username)
        logging.debug("Rx <== %s\n: %s %s"%(str(update.message.text), str(update.effective_chat.id), full_username))

        current_user = update.effective_chat
        if current_user.id not in users_cache:
            # Altera nome padrão do arquivo de configuração para conter o nome do bot
            config_default_file = f'config_{context.bot.username}.db'
            user_token = None if not current_user.id in _users_tokens else _users_tokens[current_user.id]
            save_user_rdstation(current_user.id, full_username, config_default_file, user_token)

            users_cache[current_user.id] = current_user
        else:
            config_default_file = f'config_{context.bot.username}.db'
            _users_tokens[current_user.id] = get_rdstation_token(current_user.id, db_file=config_default_file)
            user_token = None if not current_user.id in _users_tokens else _users_tokens[current_user.id]
            
        # Adiciona usuário RDStation no dicionário do Bot
        if not user_token is None:                                 
            rd_users_list = get_users_list(user_token=_users_tokens[update.effective_chat.id]) 
            _rd_users_ = rd_users_list[0]
            _current_rd_user = get_user_by_token(user_token=_users_tokens[update.effective_chat.id])
            for rd_user in _rd_users_:
                _rd_users_[update.effective_chat.id] = rd_user
                if rd_user['email'] == _current_rd_user['email']:
                    _current_rd_id[update.effective_chat.id] = rd_user['id']
                    break

        # avisa ao admin, caso não seja o próprio
        if update.effective_chat.id != config.admin_telegram_id:
            message_to_send = f"_mensagem recebida:_\n*{update.message.text}*\n_De:_*{update.effective_chat.id} @{update.effective_chat.username} {update.effective_chat.first_name}*"
            context.bot.send_message(config.admin_telegram_id, message_to_send, parse_mode=telegram.ParseMode.MARKDOWN,
                allow_sending_without_reply=True)

        # Se o comando não for /token e usuário ainda não tem token registrado, informa
        if ((update.message.text.split(' ')[0] != "/token") and (not update.effective_chat.id in _users_tokens)) \
            or ((update.message.text.split(' ')[0] != "/token") and (_users_tokens[update.effective_chat.id] is None)):
            message_to_send = f"*Você ainda não está autenticado RDStation!*\n\n"
            message_to_send += f"_Acesse sua conta pelo link https://accounts.rdstation.com.br/_\n\n"
            message_to_send += f"_No menu PERFIL, copie o TOKEN DA INSTÂNCIA!_\n"
            message_to_send += f"_Depois digite aqui o comando /token seguido do token copiado!_\n\n"
            message_to_send += f"_Exemplo:_\n"
            message_to_send += f"`/token FEfdd333r9fkdjd83dhfhu38`"
            update.message.reply_text(message_to_send, parse_mode=telegram.ParseMode.MARKDOWN,
                reply_to_message_id=update.effective_chat.id, allow_sending_without_reply=True)

    except Exception as e:
        logging.error(str(e))

# ----- Comandos do Bot para integração com RDStation

def cmd_token(update: Update, context: CallbackContext):
    try:
        try:
            config_default_file = f'config_{context.bot.username}.db'
            _users_tokens[update.effective_chat.id] = get_rdstation_token(update.effective_chat.id, db_file=config_default_file)
        except Exception as e:
            logging.error("type error: " + str(e))
            
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)

        if (not context.args is None) and (len(context.args) > 0):

            message_to_send = f"_Verificando token, aguarde...:_\n\n"
            update.message.reply_text(message_to_send, parse_mode=telegram.ParseMode.MARKDOWN,
                reply_to_message_id=update.effective_chat.id, allow_sending_without_reply=True) 

            if not check_token(user_token=context.args[0]):
                message_to_send = f"*Token inválido!:*\n\n"
                message_to_send += f"`{context.args[0]}`\n\n"
                message_to_send += f"_Acesse novamente sua conta pelo link https://accounts.rdstation.com.br/_\n\n"
                message_to_send += f"_No menu PERFIL, copie o TOKEN DA INSTÂNCIA!_\n"
                message_to_send += f"_Depois digite aqui o comando /token e cole o texto copiado!_\n\n"
                message_to_send += f"_Exemplo:_\n"
                message_to_send += f"`/token FEfdd333r9fkdjd83dhfhu38`"                
                update.message.reply_text(message_to_send, parse_mode=telegram.ParseMode.MARKDOWN,
                    reply_to_message_id=update.effective_chat.id, allow_sending_without_reply=True)  
            else:               
                message_to_send = f"*Token validado com sucesso!:*"
                update.message.reply_text(message_to_send, parse_mode=telegram.ParseMode.MARKDOWN,
                    reply_to_message_id=update.effective_chat.id, allow_sending_without_reply=True) 

                # Atualiza token do usuário
                save_user_rdstation(update.effective_chat.id, update.effective_chat.username, config_default_file, context.args[0]) 

                _users_tokens[update.effective_chat.id] = context.args[0]

                message_to_send = f"_Token do RDStation alterado com sucesso:_\n\n"
                message_to_send += f"`{_users_tokens[update.effective_chat.id]}`\n\n"

                update.message.reply_text(message_to_send, parse_mode=telegram.ParseMode.MARKDOWN,
                    reply_to_message_id=update.effective_chat.id, allow_sending_without_reply=True)

        elif update.effective_chat.id in _users_tokens  and not _users_tokens[update.effective_chat.id] is None:
                message_to_send = f"_Token do RDStation registrado neste Bot:_\n\n"
                message_to_send += f"`{_users_tokens[update.effective_chat.id]}`\n\n"
                message_to_send += f"_Para alterá-lo digite o comando /token!\n\n_"
                message_to_send += f"_Exemplo:_\n"
                message_to_send += f"`/token FEfdd333r9fkdjd83dhfhu38`"
            
                update.message.reply_text(message_to_send, parse_mode=telegram.ParseMode.MARKDOWN,
                    reply_to_message_id=update.effective_chat.id, allow_sending_without_reply=True)
        else:
            message_to_send = f"*Você ainda não está autenticado RDStation!*\n\n"
            message_to_send += f"_Acesse sua conta pelo link https://accounts.rdstation.com.br/_\n\n"
            message_to_send += f"_No menu PERFIL, copie o TOKEN DA INSTÂNCIA!_\n"
            message_to_send += f"_Depois digite aqui o comando /token e cole o texto copiado!_\n\n"
            message_to_send += f"_Exemplo:_\n"
            message_to_send += f"`/token FEfdd333r9fkdjd83dhfhu38`"
            update.message.reply_text(message_to_send, parse_mode=telegram.ParseMode.MARKDOWN,
                reply_to_message_id=update.effective_chat.id, allow_sending_without_reply=True)

    except Exception as e:
        logging.error("command_version: " + str(e))

def cmd_tasks(update: Update, context: CallbackContext):
    try:
        # verifica se o usuário já tem token registrado
        if update.effective_chat.id in _users_tokens and not _users_tokens[update.effective_chat.id] is None:
            context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)

            global _user_token
            _user_token = _users_tokens[update.effective_chat.id]

            subject_filter = ''

            # Caso tenha pelo menos um parametro, usa como filtro
            if (not context.args is None) and (len(context.args) > 0):
                subject_filter = " ".join(context.args[0:])
                
            # Obtem o id do usuário do RDStation
            if update.effective_chat.id in _rd_users_:
                rd_user = _rd_users_[update.effective_chat.id]                
                logging.debug(rd_user)

            if config.filter_by_user:
                message = get_task_list_text(
                    subject_filter=subject_filter, done_filter=config.done_filter, 
                    chat_id=update.effective_chat.id)
            else:
                message = get_task_list_text(subject_filter=subject_filter, done_filter=config.done_filter)

            logging.info(message)

            update.message.reply_text(message,parse_mode=telegram.ParseMode.HTML,
                reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)
        else:
            message_to_send = f'Usuário não autenticado!'
            logging.info(message_to_send)

    except Exception as e:
        logging.error("command_version: " + str(e))

def cmd_tasks_config(update: Update, context: CallbackContext):
    message = '_Listagem de tarefas:_\n\n'
    try:
        if (not context.args is None) and (len(context.args) > 0):
            if context.args[0] == "liga":
                config.done_filter = "nul"
            else:
                config.done_filter = "false"
                
        status = "somente abertas!" if config.done_filter == "false" else "todas"
        message += f'_Exibindo_ *{status}*'             

    except Exception as e:
        logging.error(str(e))
        message = str(e)
            
    update.message.reply_text(message,parse_mode=telegram.ParseMode.MARKDOWN,
        reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)  

def cmd_filter(update: Update, context: CallbackContext):
    message = '_Filtro por usuário:_\n\n'
    try:
        if (not context.args is None) and (len(context.args) > 0):
            if context.args[0] == "liga":
                config.filter_by_user = True
            else:
                config.filter_by_user = False
                
        status = "Ligado!" if config.filter_by_user else "Desligado!"
        message += f'*{status}*'             

    except Exception as e:
        logging.error(str(e))
        message = str(e)
            
    update.message.reply_text(message,parse_mode=telegram.ParseMode.MARKDOWN,
        reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)  

def cmd_activities(update: Update, context: CallbackContext):
    try:
        # verifica se o usuário já tem token registrado
        if update.effective_chat.id in _users_tokens and not _users_tokens[update.effective_chat.id] is None:
            context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)

            global _user_token
            _user_token = _users_tokens[update.effective_chat.id]

            subject_filter = ''

            # Caso tenha pelo menos um parametro, usa como filtro
            if (not context.args is None) and (len(context.args) > 0):
                subject_filter = " ".join(context.args[0:])

            # Caso tenha pelo menos um parametro, usa como filtro
            if (not context.args is None) and (len(context.args) > 0):
                subject_filter = " ".join(context.args[0:])
                
            # Obtem o id do usuário do RDStation
            if update.effective_chat.id in _rd_users_:
                rd_user = _rd_users_[update.effective_chat.id]                
                logging.debug(rd_user)

            if config.filter_by_user:
                message = get_activities_list_text(subject_filter=subject_filter, 
                    chat_id=update.effective_chat.id)
            else:
                message = get_activities_list_text(subject_filter=subject_filter)

            logging.info(message)

            update.message.reply_text(message,parse_mode=telegram.ParseMode.HTML,
                reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)
        else:
            message_to_send = f'Usuário não autenticado!'
            logging.info(message_to_send)

    except Exception as e:
        logging.error("command_version: " + str(e))

def cmd_deals(update: Update, context: CallbackContext):
    try:
        # verifica se o usuário já tem token registrado
        if update.effective_chat.id in _users_tokens and not _users_tokens[update.effective_chat.id] is None:
            context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)

            global _user_token
            _user_token = _users_tokens[update.effective_chat.id]

            subject_filter = ''

            # Caso tenha pelo menos um parametro, usa como filtro
            if (not context.args is None) and (len(context.args) > 0):
                subject_filter = " ".join(context.args[0:])

            # Obtem o id do usuário do RDStation
            if update.effective_chat.id in _rd_users_:
                rd_user = _rd_users_[update.effective_chat.id]                
                logging.debug(rd_user)

            if config.filter_by_user:
                message = get_deals_list_text(subject_filter=subject_filter, chat_id=update.effective_chat.id)
            else:
                message = get_deals_list_text(subject_filter=subject_filter)

            logging.info(message)

            update.message.reply_text(message,parse_mode=telegram.ParseMode.HTML,
                reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)
        else:
            message_to_send = f'Usuário não autenticado!'
            logging.info(message_to_send)

    except Exception as e:
        logging.error("command_version: " + str(e))

def cmd_users(update: Update, context: CallbackContext):
    try:
        parse_mode = telegram.ParseMode.HTML
        
        # verifica se o usuário já tem token registrado
        if update.effective_chat.id in _users_tokens and not _users_tokens[update.effective_chat.id] is None:
            context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)

            global _user_token
            _user_token = _users_tokens[update.effective_chat.id]

            subject_filter = ''
            
            message_words = update.effective_message.text.split(' ')
            
            if ( not message_words is None) and (len(message_words) > 0) and (message_words[0] == '/usuario'):
                if (not context.args is None) and (len(context.args) > 0):
                    pass
                else:
                    current_user = get_user_by_token(user_token=_users_tokens[update.effective_chat.id])
                    message = f'_Nome_: `{current_user["name"]}`\n'
                    message += f'_E-mail_: `{current_user["email"]}`\n'
                    message += f'_Empresa_: `{current_user["organization"]}`\n'
                    if update.effective_chat.id in _rd_users_:
                        message += f'_ID RDStation_: `{_rd_users_[update.effective_chat.id]}`\n'
                    if update.effective_chat.id in _users_tokens:
                        message += f'_Token RDStation_: `{_users_tokens[update.effective_chat.id]}`\n'
                    message += f'_ID Telegram_: `{update.effective_chat.id}`\n'
                    message += f'_Nome Telegram_: `{update.effective_chat.first_name} {update.effective_chat.first_name}`\n'
                    parse_mode = telegram.ParseMode.MARKDOWN
                    
            else:
                # Caso tenha pelo menos um parametro, usa como filtro
                if (not context.args is None) and (len(context.args) > 0):
                    subject_filter = " ".join(context.args[0:])

                message = get_users_list_text(subject_filter=subject_filter)

            logging.info(message)

            update.message.reply_text(message,parse_mode=parse_mode,
                reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)
        else:
            message_to_send = f'Usuário não autenticado!'
            logging.info(message_to_send)

    except Exception as e:
        logging.error(str(e))

# comando para atualizar contatos RD a partir dos usuários do Bot
def cmd_sync_to_rd(update: Update, context: CallbackContext):
    
    message = ''

    try:
        message = '<i>Sincronizando....</i>'
        update.message.reply_text(message,parse_mode= telegram.ParseMode.HTML,
            reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True) 
                
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)

        # verifica se o usuário já tem token registrado
        if update.effective_chat.id in _users_tokens and not _users_tokens[update.effective_chat.id] is None:
            
            util.util_rd_crm._user_token = _users_tokens[update.effective_chat.id]
                 
            # Sincroniza usuários do Bot com contatos do RD
            # Obtem todos os contatos do RD
            all_rd_users = util.util_rd_crm.get_users_all()
            
            # Obtem todos os usuarios do Bot
            all_bot_users = util.util_rd_crm.db_users.get_all()
            
            # Sincroniza usuários RD a partir do Bot
            util.util_rd_crm.sync_rd_from_db(
                all_rd_users= all_rd_users,
                all_bot_users= all_bot_users,
                custom_field_id= '614894fb053b7e0020f3b00b', 
                chat_custom_field_id = '5ec6d14cf02baf002e208aee',        
            ) 
            
            message = '<i>Sincronizado com sucesso!</i>'  
            
        else:
            message = '<i>Token RDStation inválido!</i>'  

    except Exception as e:
        logging.error(str(e))
        message = str(e) 
        
    update.message.reply_text(message,parse_mode= telegram.ParseMode.HTML,
        reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)        
      
# ----- Comandos administrativos

def cmd_restart(update: Update, context: CallbackContext):

    message = 'Reiniciando Bot, aguarde... ⏳'
    logging.debug(message)

    message = '_%s_'%message
    update.message.reply_text(message,parse_mode=telegram.ParseMode.MARKDOWN,
        reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)

    Thread(target=stop_and_restart).start()

def stop_and_restart():
	"""Gracefully stop the Updater and replace the current process with a new one"""
	updater.stop()
	os.execl(sys.executable, sys.executable, *sys.argv)

def cmd_shutdown(update: Update, context: CallbackContext):

    bot_name = context.bot.username
    message = "_%s %s_ *PARANDO, por favor, aguarde.... ⏳*\n`(%s)`\n`(%s)`"%(bot_name , version, config.script_name, config.host_name)
    update.message.reply_text(message,parse_mode=telegram.ParseMode.MARKDOWN,
        reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)

    os.kill(os.getpid(), signal.SIGTERM)

def cmd_version(update: Update, context: CallbackContext):
    try:
        # Use this to tell the user that something is happening on the bot's side:
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)

        message = get_bot_desc(context.bot.username)

        logging.info(message)

        update.message.reply_text(message,parse_mode=telegram.ParseMode.HTML,
            reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)

    except Exception as e:
        logging.error("command_version: " + str(e))

def cmd_page(update: Update, context: CallbackContext):
    try:
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)

        message = '_Configuração de paginação:_\n\n'
        
        # Obtem parametros de pagina atual e tamanho da pagina 
        if (not context.args is None) and (len(context.args) > 0):
            # Caso parâmetro de página atual não seja numérico, mostra exemplo
            if not context.args[0].isnumeric:
                message = f'_Número da página atual inválido:_ *{context.args[0]}*!\n\n'
                message += '_Exemplo:_\n'
                message += '`/pag 2` _(altera página atual para 2)_\n'
            else:                
                # TODO : Caso tenha mais de um parâmetro, altera tamanho da página
                if len(context.args) > 1:
                    message += f'*Página atual a ser exibida: {config.page_start}*\n\n'        
                    message += f'*Quantidade de itens por página: {config.page_size}*\n\n'                        
                else:
                    message += f'*Página atual a ser exibida: {config.page_start}*\n\n'        
                    message += f'*Quantidade de itens por página: {config.page_size}*\n\n'    
        else:
            message += f'*Página atual a ser exibida: {config.page_start}*\n\n'        
            message += f'*Quantidade de itens por página: {config.page_size}*\n\n'        

        logging.info(message)

        update.message.reply_text(message,parse_mode=telegram.ParseMode.MARKDOWN,
            reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)

    except Exception as e:
        logging.error(str(e))

def cmd_list_admin(update: Update, context: CallbackContext):
    try:
        response_message = ''

        if len(context.args) == 0:
            response_message = '_ 👨‍🎓 Administradores:_' + os.linesep
            for user in config.admin_group:
                if user in users_cache:
                    response_message += '`%s %s\n`'%(str(user), str(users_cache[user]['first_name']))
                else:
                    response_message += '`%s \n`'%(str(user))
        else:
            # verifica se o parametro é um número inteiro válido
            new_user = 0
            try:    
                new_user = int(context.args[0])
                if new_user in config.admin_group:
                    config.admin_group.remove(new_user)
                    response_message = '_Usuário_ *%d removido* _do grupo_ *admin!*'%new_user
                else:
                    config.admin_group.append(new_user)
                    response_message = '_Usuário_ *%d adicionado* _ao grupo_ *admin!*'%new_user
                
                main_commands(context.dispatcher)

            except:
                response_message = '*ID do usuário não é válido no comando.*\r\n_Exemplo: /admin 12345_'

        update.message.reply_text(response_message, \
            parse_mode=telegram.ParseMode.MARKDOWN, \
            reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)              

    except Exception as e:
        logging.error(str(e))    

def cmd_checkbox(update: Update, context: CallbackContext):
    pass

# ----- Comandos gerais

def cmd_start(update: Update, context: CallbackContext) -> None:
	"""Send a message when the command /start is issued."""
	context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)
	update.message.reply_text(config.start_message%context.bot.username, parse_mode=telegram.ParseMode.MARKDOWN, 
		reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)

def cmd_help(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""

    try:
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)

        help_message = ''

        # Caso o usuário atual seja admin, mostra ajuda de todos os comandos
        # if update.effective_chat.id == config.admin_telegram_id:
        if update.effective_chat.id in config.admin_group:
            help_message = config.help_text_admin
        else: 	
            help_message = config.help_text

        try:
            try:
                update.message.reply_text(help_message, \
                    parse_mode=telegram.ParseMode.MARKDOWN, \
                    reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)
            except Exception as e:
                logging.error(str(e))			

        except Exception as e:
            logging.error(str(e))
            update.message.reply_text(help_message, \
                reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)      

    except Exception as e:
        logging.error(str(e)) 

def cmd_listusers(update: Update, context: CallbackContext):
	try:
		list_page = 1
		users_filter = None
		if (not context.args is None) and (len(context.args) > 0) and (context.args[0].isnumeric()):
			list_page = int(context.args[0])
		elif  (not context.args is None) and (len(context.args) > 0):
			users_filter = " ".join(context.args)

		all_users = '_  👫 Somente usuários autorizados:_' + os.linesep
		
		# users_cache = global_vars.users_cache
		users_cache = global_vars.users_cache
		# Python 3
		# first2pairs = {k: mydict[k] for k in list(mydict)[:2]}
		users_cache = {k: global_vars.users_cache[k] for k in list(global_vars.users_cache)[(list_page - 1)* 100 : list_page * 100]}

		# obtem todos os usuarios, limitando ao máximo de 100 usuários
		util_config.all_users = util_config.get_all_users(list_page * 100, filter=users_filter) 		

		for user in users_cache:
			try:

				is_user_in_db = False

				for user_db in util_config.all_users:
					if user in user_db:
						is_user_in_db = True
						break
				
				if not is_user_in_db:
					continue

				user_balance = 0
				try: 
					user_element = list(filter(lambda c: c[1] == user, util_config.all_users))
					# user_balance = 0 if (user_element == None) or (len(user_element)==0) or (len(user_element[0])<5) else user_element[0][3]
					user_balance = 0 # util_pay_stripe.update_user_balance(user, 0, update, context, do_not_warn=True)
				except Exception as e:
					logging.error(str(e))  				

				if(type(users_cache[user]) is str):
					# all_users += '`%s %s\n`'%(str(user), users_cache[user])
					# '{:10s} {:3d}  {:7.2f}'.format('xxx', 123, 98)
					# xxx        123    98.00
					all_users +='`{:10s} {:13s} R${:>5s}`\n'.format(str(user), users_cache[user][:13], f'{str(user_balance/100)}0')
					# all_users += '`{0:<10s} {0:<20s} {0:>10s}`\n'.format(str(user)[:10], users_cache[user][:30], 'R$ 10,00')
				else:
					full_name = users_cache[user].first_name + ' ' + users_cache[user].last_name + ' @' + str(users_cache[user].username)
					# all_users += '`%s %s\n`'%(str(user), full_name)
					all_users +='`{:10s} {:13s} R${:>5s}`\n'.format(str(user), full_name[:13], f'{str(user_balance/100)}0')
			except Exception as e:  
				log_message = "_Error:_\n*%s*\n*%s*"%(update.message.text, str(e))  
				logging.error(log_message)   
				all_users = log_message  

		if all_users is not None:
			first_row = ((list_page - 1)* 100)+1
			last_row = (list_page * 100)
			if last_row > len(global_vars.users_cache) :
				last_row = len(global_vars.users_cache) 
			if first_row < len(global_vars.users_cache) :
				all_users += f"""\n*De {first_row} até {last_row} / {len(global_vars.users_cache)}*""" 
			else:
				all_users += f'Página {list_page} maior que a qtd de usuários: {len(global_vars.users_cache)}'

		if update.message is None:
			context.bot.send_message(
				chat_id = update.effective_chat.id,
				text = all_users, 
				parse_mode=telegram.ParseMode.MARKDOWN) 
		else:
			update.message.reply_text(all_users, \
				parse_mode=telegram.ParseMode.MARKDOWN, \
				reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)              

	except Exception as e:
		log_message = "_Error:_\n*%s*\n*%s*"%(update.message.text, str(e))
		logging.error(log_message)       
		update.message.reply_text(log_message, \
			parse_mode=telegram.ParseMode.MARKDOWN, \
						reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)

def cmd_get_bot_users(update: Update, context: CallbackContext):

    response_message = ''
    
    try:
        all_bot_users = db_users.get_all()
        if (not context.args is None) and (len(context.args) == 0) and (update.message.text == '/contatos'):
            if (not all_bot_users is None) and (len(all_bot_users) > 0):
                response_message = '_Usuários do Bot_'
                counter = 1
                for bot_user in all_bot_users:
                    chat_id = '{:>10s}'.format(str(bot_user.chat_id))
                    user_name = '{:10s}'.format(str(bot_user.user_name))
                    # response_message += f'\n_{counter}_ `{chat_id}` '
                    # response_message += f'`{user_name}`'
                    is_rd_user = '{:2s}'.format('RD') if bot_user.rdstation_id else ''
                    # response_message += f' *{is_rd_user}*
                    # https://unicode.org/emoji/charts/full-emoji-list.html
                    # https://apps.timwhitlock.info/emoji/tables/unicode
                    response_message += '\n`{:>10s} {:10s}` ✔ */RD{:1s}*'.format(str(bot_user.chat_id), bot_user.user_name[:10], str(counter))
                    counter += 1
            else:
                response_message = '_Nenhum usuário cadastrado no Bot_'

        else:
            bot_user = None
            if (not context.args is None) and len(context.args) > 0:
                bot_user = db_users.get_user_by_id(context.args[0])
            else:
                user_index = int(update.message.text[3:]) - 1
                bot_user = [all_bot_users[user_index]]
            
            # Obtem contato RD do usário
            rd_contactList = util.util_rd_crm.get_contacts(
                contact_id=bot_user[0].rdstation_id,
                user_token=_users_tokens[update.effective_chat.id]
                )    
            
            response_message = f'\n_Contato RDStation_\n'    
            response_message += f'\n_Nome_\n`{rd_contactList[0]["name"]}`'    
            response_message += f'\n_Id_\n`{rd_contactList[0]["id"]}`'    

    except Exception as e:
        response_message = str(e)
        logging.error(response_message)  
             
    update.message.reply_text(response_message, \
        parse_mode=telegram.ParseMode.MARKDOWN, \
                    reply_to_message_id=update.effective_message.message_id, allow_sending_without_reply=True)    

# ------ Funções principais

def get_bot_desc(bot_name:str):
    message = ''
    try:
        message = '<i>Versão atual:</i> <b>%s</b>'%version
        message += '\n<i>Nome do Bot:</i> <b>%s</b>'%str(bot_name)
        message += '\n\n<i>Script:</i> \n<b>%s</b>'%config.script_name
        message += '\n\n<i>Servidor:</i> <b>%s</b>'%config.host_name
        message += '\n\n<i>Linha de comando:</i>\n<b>%s</b>'%" ".join(sys.argv[:])

    except Exception as e:
        logging.error(str(e))

    return message

def main_commands(dispatcher: Dispatcher):
    
    try:  
        # obtem cache de usuario a partir do b.d. local de configuração
        # global_vars.users_cache = util_config.get_all_users_id_name()              
        # Obtem todos os usuarios do Bot
        # all_bot_users = db_users.get_all()
        
        # TODO: atualizar e criar usuários no Bot a partir do RD (?)
           
        # Tratamentos comuns a todas as mensagens
        dispatcher.add_handler(MessageHandler(Filters.all, global_handler), -1)

        # Registra comandos básicos para todos os usuários
        dispatcher.add_handler(CommandHandler("start", cmd_start), 1)
        dispatcher.add_handler(CommandHandler("help", cmd_help), 1)        

        dispatcher.add_handler(CommandHandler("tarefas", cmd_tasks), 1)
        dispatcher.add_handler(CommandHandler("tconfig", cmd_tasks_config), 1)
        dispatcher.add_handler(CommandHandler("filtro", cmd_filter), 1)
        dispatcher.add_handler(CommandHandler("anota", cmd_activities), 1)
        dispatcher.add_handler(CommandHandler("oport", cmd_deals), 1)
        
        dispatcher.add_handler(CommandHandler("token", cmd_token), 1)
        dispatcher.add_handler(CommandHandler("sync", cmd_sync_to_rd), 1)
        dispatcher.add_handler(CommandHandler("usuarios", cmd_users), 1)
        dispatcher.add_handler(CommandHandler("usuario", cmd_users), 1)
        
        dispatcher.add_handler(CommandHandler("contatos", cmd_get_bot_users), 1)
        dispatcher.add_handler(CommandHandler("rd", cmd_get_bot_users, 
            filters=Filters.user(config.admin_group)), 1)        
        # dispatcher.add_handler(CommandHandler(("RD1", "RD2", "RD3"), cmd_get_bot_users, 
        #     filters=Filters.user(config.admin_group)), 1)       
        dispatcher.add_handler(CommandHandler("rdn", cmd_checkbox, 
            filters=Filters.user(config.admin_group)), 1)
        updater.dispatcher.add_handler(
            MessageHandler(
                Filters.command & Filters.regex(pattern=re.compile('RD', re.IGNORECASE)),
                cmd_get_bot_users
            )
        )        

        # Comandos administrativos
        dispatcher.add_handler(CommandHandler("ver", cmd_version,
            filters=Filters.user(config.admin_group)), 1)
        
        dispatcher.add_handler(CommandHandler("pag", cmd_page,
            filters=Filters.user(config.admin_group)), 1)

        dispatcher.add_handler(CommandHandler("restart", cmd_restart,
            filters=Filters.user(config.admin_group)), 1)

        dispatcher.add_handler(CommandHandler("stop", cmd_shutdown,
            filters=Filters.user(config.admin_group)), 1)

        dispatcher.add_handler(CommandHandler("admin", cmd_list_admin, 
            filters=Filters.user(config.admin_group)), 1)	

    except Exception as e:
        logging.error(str(e))

# ------ Funções auxiliares

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

# --- Consulta genérica a banco de dados SQLite
def execute_query(query: str, db_file:str = None):
    
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

# ------------------------------------------
# ---------------- Token Exibir / Verificar https://plugcrm.net/api/v1/token/check     
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

def check_token(base_url:str = None, user_token:str = None)->bool:

    result = False

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        tasks_response = get_token(
            base_url=base_url, user_token=user_token
            )

        if tasks_response.ok:
            tasks_object = json.loads(tasks_response.text)
            total_tasks = tasks_object['name']
            result = True

    except Exception as e:
        logging.error(str(e))

    return result

def get_user_by_token(base_url:str = None, user_token:str = None):

    result = None

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        tasks_response = get_token(
            base_url=base_url, user_token=user_token
            )

        if tasks_response.ok:
            result = json.loads(tasks_response.text)

    except Exception as e:
        logging.error(str(e))

    return result

# ------------------------------------------
# ---------------- Tarefas
# ------------------------------------------

# ------- Listagem de tarefas
def get_tasks(
    deal_id:str = '', base_url:str = None, user_token:str = None, subject_filter:str = None,
    page_number:int = 1, page_limit:int = 20, done_filter: str = "false"
    , chat_id:str = None
    ):

    response = None

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        url = f"{base_url}/tasks"

        user_id = ''
        if not chat_id is None:
            user_id = _current_rd_id[chat_id]
        
        # restringe somente tarefas em aberto
        # done=true|false|nul
        payload = json.dumps({
            "token": f"{user_token}",
            "limit": page_limit,
            "page": page_number,
            "deal_id": f"{deal_id}",
            "done" : f"{done_filter}",
            "user_id": f'{user_id}'
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

    except Exception as e:
        logging.error(str(e))

    return response

def get_task_list(base_url:str = None, user_token:str = None, subject_filter:str = None,
    page_number:int = 1, page_limit:int = 20, done_filter: str = "false"
    , chat_id:str = None):

    task_list = []
    total_tasks = 0
    has_more = False
    page_size = 0

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        tasks_response = get_tasks(
            base_url=base_url, user_token=user_token,
            page_limit=page_limit, page_number=page_number, done_filter=done_filter
            )

        if tasks_response.ok:
            tasks_object = json.loads(tasks_response.text)
            total_tasks = tasks_object['total']
            has_more = tasks_object['has_more']
            page_size = len(tasks_object['tasks'])
            for task in tasks_object['tasks']:
                logging.debug(task['subject'])
                task_list.append(task)

    except Exception as e:
        logging.error(str(e))

    return task_list, total_tasks, has_more, page_size

def get_task_list_text(
    base_url:str = None, user_token:str = None, subject_filter:str = None
    , done_filter: str = "false"
    , chat_id:str = None
    ):

    task_list_text = 'Nenhuma tarefa encontrada!'

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        page_number = 1
        page_limit = 20

        tasks_list, total_tasks, has_more, page_size = get_task_list(
            base_url=base_url, user_token=user_token, subject_filter=subject_filter
            , done_filter=done_filter, chat_id=chat_id
            )

        if not tasks_list is None:
            task_counter = 1
            task_list_text = '' # '<b>Lista de Tarefas:</b>'
            for task in tasks_list:
                logging.debug(task)
                if (subject_filter is None) or subject_filter.lower() in str(task["subject"]).lower():
                    task_list_text += f'\n<i>{task_counter}</i>: <code>{task["subject"]}</code>'
                    task_counter += 1

            page_count = int(total_tasks/page_limit)
            if (total_tasks % page_limit) > 0:
                page_count += 1

            first_row_number = ((page_number - 1) * page_limit) + 1
            last_row_number = (page_number * page_limit)

            task_list_text += f'\n\n<i>Página:</i> <b>{page_number}/{page_count}</b>'
            task_list_text += f'\n<i>Filtro:</i> <b>{"todos" if subject_filter == "" else subject_filter}</b>'
            task_list_text += f'\n<i>Encontrados/lidos:</i> <b>{task_counter - 1}/{page_size}</b>'
            task_list_text += f'\n<i>Total de tarefas:</i> <b>{total_tasks}</b>'
            task_list_text += f'\n\n<i>Para exibir somente tarefas selecionadas use:</i>'
            task_list_text += f'\n<code>/tarefas texto selecionado</code>'

    except Exception as e:
        logging.error(str(e))

    return task_list_text

# ------- Criação de tarefas
def put_tasks(deal_id:str, base_url:str = None, user_token:str = None):

    if base_url is None:
        base_url = _base_url

    if user_token is None:
        user_token = _user_token

    url = f"{base_url}/tasks"

    payload = json.dumps({
        "token": f"{user_token}",
        "task": {
            "deal_id": f"{deal_id}",
            "user_ids": [
                "Código do usuário"
            ],
            "subject": "Assunto",
            "type": "Tipo",
            "hour": "Hora",
            "date": "Data",
            "notes": "Anotações"
        }
    })

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

# ------------------------------------------
# ---------------- Anotações
# ------------------------------------------

# ------- Listagem de anotações
def get_activities(
    deal_id:str = '', base_url:str = None, user_token:str = None, subject_filter:str = None,
    page_number:int = 1, page_limit:int = 20
    , chat_id:str = None
    ):

    response = None

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        url = f"{base_url}/activities"
        
        user_id = ''
        if not chat_id is None:
            user_id = _current_rd_id[chat_id]
            
        payload = json.dumps({
            "token": f"{user_token}",
            "deal_id": f"{deal_id}",
            "user_id": f'{user_id}'
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

    except Exception as e:
        logging.error(str(e))

    return response

def get_activities_list(base_url:str = None, user_token:str = None, subject_filter:str = None,
    page_number:int = 1, page_limit:int = 20
    , chat_id:str = None):

    activities_list = []
    activities_tasks = 0
    has_more = False
    page_size = 0

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        activities_response = get_activities(
            base_url=base_url, user_token=user_token,
            page_limit=page_limit, page_number=page_number
            , chat_id=chat_id
            )

        if activities_response.ok:
            activities_object = json.loads(activities_response.text)
            page_size = len(activities_object['activities'])
            for activity in activities_object['activities']:
                logging.debug(activity['text'])
                activities_list.append(activity)

    except Exception as e:
        logging.error(str(e))

    return activities_list, page_size

def get_activities_list_text(base_url:str = None, user_token:str = None, subject_filter:str = None
    , chat_id:str = None):

    activities_list_text = 'Nenhuma anotação encontrada!'

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        page_number = 1
        page_limit = 10

        activities_list, page_size = get_activities_list(
            base_url=base_url, user_token=user_token, subject_filter=subject_filter
            , chat_id=chat_id
            )

        if not activities_list is None:
            activities_counter = 1
            activities_list_text = '' # '<b>Lista:</b>'
            for activity in activities_list[:page_limit]:
                logging.debug(activity)
                if (subject_filter is None) or subject_filter.lower() in str(activity["text"]).lower():
                    activities_list_text += f'\n<i>{activities_counter}</i>: <code>{activity["text"]}</code>'
                    activities_counter += 1

            page_count = int(page_size/page_limit)
            if (page_size % page_limit) > 0:
                page_count += 1

            first_row_number = ((page_number - 1) * page_limit) + 1
            last_row_number = (page_number * page_limit)

            activities_list_text += f'\n\n<i>Página:</i> <b>{page_number}/{page_count}</b>'
            activities_list_text += f'\n<i>Filtro:</i> <b>{"todos" if subject_filter == "" else subject_filter}</b>'
            activities_list_text += f'\n<i>Encontrados/lidos:</i> <b>{activities_counter - 1}/{page_size}</b>'
            activities_list_text += f'\n<i>Total:</i> <b>{page_size}</b>'
            activities_list_text += f'\n\n<i>Para exibir somente selecionadas use:</i>'
            activities_list_text += f'\n<code>/atividades texto selecionado</code>'

    except Exception as e:
        logging.error(str(e))

    return activities_list_text

# ------------------------------------------
# ---------------- Oportunidades
# ------------------------------------------

# ------- Listar Oportunidades
def get_deals(
    deal_id:str = '', base_url:str = None, user_token:str = None, subject_filter:str = None,
    page_number:int = 1, page_limit:int = 20, chat_id:str = None
    ):

    response = None

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        user_id = ''
        if not chat_id is None:
            user_id = _current_rd_id[chat_id]
            
        url = f"{base_url}/deals"
        #  https://plugcrm.net/api/v1/deals?token=MyTOKEN&Parametros

        payload = json.dumps({
            "token": f"{user_token}",
            "user_id": f'{user_id}'
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

    except Exception as e:
        logging.error(str(e))

    return response

def get_deals_list(base_url:str = None, user_token:str = None, subject_filter:str = None,
    page_number:int = 1, page_limit:int = 20, chat_id:str = None):

    deals_list = []
    deals_tasks = 0
    has_more = False
    page_size = 0

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        deals_response = get_deals(
            base_url=base_url, user_token=user_token,
            page_limit=page_limit, page_number=page_number, chat_id=chat_id
            )

        if deals_response.ok:
            deals_object = json.loads(deals_response.text)
            page_size = len(deals_object['deals'])
            for deal in deals_object['deals']:
                logging.debug(deal['name'])
                deals_list.append(deal)

    except Exception as e:
        logging.error(str(e))

    return deals_list, page_size

def get_deals_list_text(
    base_url:str = None, user_token:str = None, subject_filter:str = None
    , chat_id:str = None
    ):

    deals_list_text = 'Nenhuma anotação encontrada!'

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        page_number = 1
        page_limit = 10

        deals_list, page_size = get_deals_list(
            base_url=base_url, user_token=user_token, subject_filter=subject_filter
            , chat_id=chat_id
            )

        if not deals_list is None:
            deals_counter = 1
            deals_list_text = '' # '<b>Lista de Anotações:</b>'
            for deal in deals_list[:page_limit]:
                logging.debug(deal)
                if (subject_filter is None) or subject_filter.lower() in str(deal["name"]).lower():
                    deals_list_text += f'\n<i>{deals_counter}</i>: <code>{deal["name"]}</code>'
                    deals_counter += 1

            page_count = int(page_size/page_limit)
            if (page_size % page_limit) > 0:
                page_count += 1

            first_row_number = ((page_number - 1) * page_limit) + 1
            last_row_number = (page_number * page_limit)

            deals_list_text += f'\n\n<i>Página:</i> <b>{page_number}/{page_count}</b>'
            deals_list_text += f'\n<i>Filtro:</i> <b>{"todos" if subject_filter == "" else subject_filter}</b>'
            deals_list_text += f'\n<i>Encontrados/lidos:</i> <b>{deals_counter - 1}/{page_size}</b>'
            deals_list_text += f'\n<i>Total de anotações:</i> <b>{page_size}</b>'
            deals_list_text += f'\n\n<i>Para exibir somente anotações selecionadas use:</i>'
            deals_list_text += f'\n<code>/anota texto selecionado</code>'

    except Exception as e:
        logging.error(str(e))

    return deals_list_text

# ------------------------------------------
# ---------------- Usuários https://plugcrm.net/api/v1/users?token=MyTOKEN
# ------------------------------------------

# ------- Listar Usuários
def get_users(
    deal_id:str = '', base_url:str = None, user_token:str = None, subject_filter:str = None,
    page_number:int = 1, page_limit:int = 20, user_id:str = None
    ):

    response = None

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        url = f"{base_url}/users"

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

def get_users_list(base_url:str = None, user_token:str = None, subject_filter:str = None,
    page_number:int = 1, page_limit:int = 20, user_id:str = None):

    deals_list = []
    deals_tasks = 0
    has_more = False
    page_size = 0

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        response = get_users(
            base_url=base_url, user_token=user_token,
            page_limit=page_limit, page_number=page_number
            )

        if response.ok:
            response_object = json.loads(response.text)
            page_size = len(response_object['users'])
            for item in response_object['users']:
                logging.debug(item['name'])
                deals_list.append(item)

    except Exception as e:
        logging.error(str(e))

    return deals_list, page_size

def get_users_list_text(base_url:str = None, user_token:str = None, subject_filter:str = None):

    deals_list_text = 'Nenhuma anotação encontrada!'

    try:
        if base_url is None:
            base_url = _base_url

        if user_token is None:
            user_token = _user_token

        page_number = 1
        page_limit = 10

        deals_list, page_size = get_users_list(
            base_url=base_url, user_token=user_token, subject_filter=subject_filter
            )

        if not deals_list is None:
            deals_counter = 1
            deals_list_text = '' # '<b>Lista:</b>'
            for deal in deals_list[:page_limit]:
                logging.debug(deal)
                if (subject_filter is None) or subject_filter.lower() in str(deal["name"]).lower():
                    deals_list_text += f'\n<i>{deals_counter}</i>: <code>{deal["name"]}</code>'
                    deals_counter += 1

            page_count = int(page_size/page_limit)
            if (page_size % page_limit) > 0:
                page_count += 1

            first_row_number = ((page_number - 1) * page_limit) + 1
            last_row_number = (page_number * page_limit)

            deals_list_text += f'\n\n<i>Página:</i> <b>{page_number}/{page_count}</b>'
            deals_list_text += f'\n<i>Filtro:</i> <b>{"todos" if subject_filter == "" else subject_filter}</b>'
            deals_list_text += f'\n<i>Encontrados/lidos:</i> <b>{deals_counter - 1}/{page_size}</b>'
            deals_list_text += f'\n<i>Total:</i> <b>{page_size}</b>'
            deals_list_text += f'\n\n<i>Para exibir somente selecionados use:</i>'
            deals_list_text += f'\n<code>/usu texto selecionado</code>'

    except Exception as e:
        logging.error(str(e))

    return deals_list_text

# ----------------

def main():

    # set up logging to standard output
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        # Adiciona o dono do bot ao grupo de administradores
        config.admin_group.append(config.admin_telegram_id)
        
        # Cria arquivo de b.d. de configuração de usuários e tabelas necessárias
        create_table_sql = """
            CREATE TABLE "users" 
            (  
                "id"    INTEGER,        
                "chat_id"       INTEGER NOT NULL UNIQUE,        
                "user_name"     TEXT NOT NULL, 
                balance decimal default 0, 
                phone text, 
                rdstation_token text,   
                PRIMARY KEY("id") 
            );
            """
        execute_query(create_table_sql)

        message = f"⏳<b>Iniciando...</b>{os.linesep}{os.linesep}{get_bot_desc(updater.bot.username)}"
        updater.bot.send_message(chat_id=config.admin_telegram_id, text=message, parse_mode=parsemode.ParseMode.HTML)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # Comandos administrativos
        main_commands(dispatcher)

        message = f"<b>INICIADO</b> com sucesso! ☑{os.linesep}{os.linesep}{get_bot_desc(updater.bot.username)}"
        updater.bot.send_message(chat_id=config.admin_telegram_id, text=message, parse_mode=parsemode.ParseMode.HTML)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()

        message = f"<b>PARADO!</b>\n{os.linesep}{os.linesep}{get_bot_desc(updater.bot.username)}"
        updater.bot.send_message(chat_id=config.admin_telegram_id, text=message, parse_mode=parsemode.ParseMode.HTML)

    except Exception as e:
        logging.error(str(e))

def unit_test():

    global _user_token
    
    _user_token = sys.argv[3]    
    deals_list_text = get_deals_list_text(user_token=_user_token)
    logging.debug(deals_list_text)  

if __name__ == '__main__':
    # unit_test()

    main()

