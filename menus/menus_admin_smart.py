#!/usr/bin/env python3.7
"""#!/usr/bin/env python3.8"""

# https://stackoverflow.com/questions/51125356/proper-way-to-build-menus-with-python-telegram-bot

version = '8.9.0 - Ativa ou desativa interface de botões com menus '

import os
import sys

import logging
import telegram

from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler

from telegram.parsemode import ParseMode

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f'{path}/..')

import bot_config as config
import bot_config

from telegram.ext import Updater, Dispatcher
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import CallbackContext
# import telegram

import trackfreeze

#https://github.com/tezmen/tg-magic/blob/master/tgmagic/bot.py

############################### Bot ############################################

def main_menu(bot:Update, update:CallbackContext):

  if not bot.effective_chat.id in config.admin_group:
    return

  if bot.callback_query is None:
    bot.message.reply_text(main_menu_message(),
                          reply_markup=main_menu_keyboard(),
                            parse_mode=ParseMode.MARKDOWN) 
  else:                             
    bot.callback_query.message.edit_text(main_menu_message(),
                            reply_markup=main_menu_keyboard(),
                            parse_mode=ParseMode.MARKDOWN)

def second_menu(bot, update):
  bot.callback_query.message.edit_text(second_menu_message(),
                          reply_markup=second_menu_keyboard(),
                          parse_mode=ParseMode.MARKDOWN)
# ------------------------

def first_menu(bot:Update, update:CallbackContext):
  bot.callback_query.message.edit_text(first_menu_message(),
                          reply_markup=first_menu_keyboard(),
                          parse_mode=ParseMode.MARKDOWN
                          )

def submenu_11(bot, update):
  bot.callback_query.message.edit_text(menu_11_message(),
                          reply_markup=menu_11_keyboard(),
                          parse_mode=ParseMode.MARKDOWN
                          ) 

def submenu_11_1(update: Update, context: CallbackContext):
  context.user_data['choice'] = update.effective_message.text  
  trackfreeze.cmd_list_hist(update, context)

def submenu_11_2(update: Update, context: CallbackContext):
  trackfreeze.cmd_imap_test(update, context)

# Bots
def submenu_12(update: Update, context: CallbackContext):
  update.callback_query.message.edit_text(menu_12_message(),
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=menu_12_keyboard()) 

# Bots - Exibir cmd_bots_list
def submenu_12_1(update: Update, context: CallbackContext):
  trackfreeze.cmd_bots_list(update, context)

# Bots - Gerenciar cmd_bot_token
def submenu_12_2(update: Update, context: CallbackContext):
    trackfreeze.cmd_bot_token(update, context)

# ------------------------

def second_menu_keyboard():
  keyboard = [[InlineKeyboardButton('Clientes e Usuários', callback_data='m2_1')],
              [InlineKeyboardButton('Bots', callback_data='m2_2')],
              [InlineKeyboardButton('<- Voltar', callback_data='main')]]
  return InlineKeyboardMarkup(keyboard)

def menu_21_keyboard():
  keyboard = [[InlineKeyboardButton('Listar Clientes/Usuário', callback_data='m21_1')],
              [InlineKeyboardButton('Gerenciar Clientes/Usuários', callback_data='m21_2')],
              [InlineKeyboardButton('<- Voltar', callback_data='menu2')]]
  return InlineKeyboardMarkup(keyboard)

def submenu_21(update: Update, context: CallbackContext):
    update.callback_query.message.edit_text(menu_21_message(),
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=menu_21_keyboard())     

def submenu_21_1(update: Update, context: CallbackContext):
    trackfreeze.cmd_listusers(update, context) 

def submenu_21_2(update: Update, context: CallbackContext):
    trackfreeze.cmd_listusers_all(update, context) 

def menu_22_keyboard():
  keyboard = [[InlineKeyboardButton('Exibir Bots', callback_data='m22_1')],
              [InlineKeyboardButton('Gerenciar Bots', callback_data='m22_2')],
              [InlineKeyboardButton('<- Voltar', callback_data='menu2')]]
  return InlineKeyboardMarkup(keyboard)

def submenu_22(update: Update, context: CallbackContext):
    update.callback_query.message.edit_text(menu_22_message(),
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=menu_22_keyboard())    

def submenu_22_1(update: Update, context: CallbackContext):
    trackfreeze.cmd_config(update, context)   

def submenu_22_2(update: Update, context: CallbackContext):
    trackfreeze.cmd_config(update, context)

# ------------------------

def third_menu_keyboard():
  keyboard = [[InlineKeyboardButton('Configurar e-mail', callback_data='m3_1')],
              [InlineKeyboardButton('Configurar alarmes', callback_data='m3_2')],
              [InlineKeyboardButton('Configurar bot', callback_data='m3_2')],
              [InlineKeyboardButton('<- Voltar', callback_data='main')]]
  return InlineKeyboardMarkup(keyboard)

def third_menu(bot, update):
  bot.callback_query.message.edit_text(third_menu_message(),
                          reply_markup=third_menu_keyboard(),
                          parse_mode=ParseMode.MARKDOWN)

def menu_31_keyboard():
  keyboard = [
              [
                InlineKeyboardButton('E-mail configurado (/config)', callback_data='m31_1'),
                InlineKeyboardButton('Liga/desliga Log (/imaplog)', callback_data='m3111')
              ],
              [
                InlineKeyboardButton('Exibir filtros de e-mail', callback_data='m31_2'),
                InlineKeyboardButton('Alterar filtros de e-mail', callback_data='m31_2')
              ],
              [InlineKeyboardButton('<- Voltar', callback_data='menu3')]]
  return InlineKeyboardMarkup(keyboard)

def menu_32_keyboard():
  keyboard = [[InlineKeyboardButton('Alarme de voz', callback_data='m32_1')],
              [InlineKeyboardButton('Alarme SMS', callback_data='m32_2')],
              [InlineKeyboardButton('Alarme Zap', callback_data='m32_3')],
              [InlineKeyboardButton('<- Voltar', callback_data='menu3')]]
  return InlineKeyboardMarkup(keyboard)

def submenu_31(update: Update, context: CallbackContext):
    update.callback_query.message.edit_text(menu_31_message(),
                            reply_markup=menu_31_keyboard())             

def submenu_31_1(update: Update, context: CallbackContext):
    trackfreeze.cmd_config(update, context)

def submenu_31_11(update: Update, context: CallbackContext):
    trackfreeze.cmd_imap_log_toggle(update, context)

def submenu_31_2(update: Update, context: CallbackContext):
    trackfreeze.cmd_filter_alarms(update, context)

def submenu_32(update: Update, context: CallbackContext):
    update.callback_query.message.edit_text(menu_32_message(),
                            reply_markup=menu_32_keyboard())              

def submenu_32_1(update: Update, context: CallbackContext):
    trackfreeze.cmd_voice(update, context)

def submenu_32_2(update: Update, context: CallbackContext):
    trackfreeze.cmd_sms_toggle(update, context)

def submenu_32_3(update: Update, context: CallbackContext):
    trackfreeze.cmd_zap_toggle(update, context)

# ------------------------

# def error(update, context):
def error(update: Update, context: CallbackContext):
    print(f'Update {update} caused error {context.error}')
    # context.bot.message.reply_text(f'{context.error}')
    context.bot.send_message(update.effective_user.id, f'{context.error}')

############################ Keyboards #########################################
def main_menu_keyboard():
  keyboard = [[InlineKeyboardButton('Monitorar', callback_data='menu1'),
              InlineKeyboardButton('Gerenciar', callback_data='menu2')],
              [InlineKeyboardButton('Configurar', callback_data='menu3')]
              ]
  return InlineKeyboardMarkup(keyboard)

def first_menu_keyboard():
  keyboard = [[InlineKeyboardButton('Alarmes', callback_data='m1_1')],
              [InlineKeyboardButton('Bots', callback_data='m1_2')],
              [InlineKeyboardButton('<- Voltar', callback_data='main')]]
  return InlineKeyboardMarkup(keyboard)

def menu_11_keyboard():
  keyboard = [[InlineKeyboardButton('Histórico', callback_data='m11_1')],
              [InlineKeyboardButton('Teste', callback_data='m11_2 Teste')],
              [InlineKeyboardButton('<- Voltar', callback_data='menu1')]]
  return InlineKeyboardMarkup(keyboard)

def menu_12_keyboard():
  keyboard = [[InlineKeyboardButton('Exibir', callback_data='m12_1')],
              [InlineKeyboardButton('Gerenciar', callback_data='m12_2')],
              [InlineKeyboardButton('<- Voltar', callback_data='menu1')]]
  return InlineKeyboardMarkup(keyboard)

############################# Messages #########################################
def main_menu_message():
  return '*Menu Principal*'

def first_menu_message():
  return '*Monitorar*'

def second_menu_message():
  return '*Gerenciar*'

def third_menu_message():
  return '*Configurar*'

def menu_11_message():
  return '*Monitorar - Alarmes*'

def menu_12_message():
  return '*Bots*'

def menu_21_message():
  return '*Gerenciar *'

def menu_22_message():
  return 'Escolha uma opção:'

def menu_31_message():
  return 'Escolha uma opção:'

def menu_32_message():
  return 'Escolha uma opção:'

############################# Handlers #########################################

def main_commands(dispatcher: Dispatcher):
    try:

      dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
      # , filters=Filters.user(config.admin_group)

      dispatcher.add_handler(CallbackQueryHandler(first_menu, pattern='menu1'))
      dispatcher.add_handler(CallbackQueryHandler(second_menu, pattern='menu2'))
      dispatcher.add_handler(CallbackQueryHandler(third_menu, pattern='menu3'))

      dispatcher.add_handler(CallbackQueryHandler(submenu_11, pattern='m1_1'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_12, pattern='m1_2'))

      dispatcher.add_handler(CallbackQueryHandler(submenu_11_1, pattern='m11_1'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_11_2, pattern='m11_2'))

      dispatcher.add_handler(CallbackQueryHandler(submenu_12_1, pattern='m12_1'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_12_2, pattern='m12_2'))

      dispatcher.add_handler(CallbackQueryHandler(submenu_21, pattern='m2_1'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_22, pattern='m2_2'))

      dispatcher.add_handler(CallbackQueryHandler(submenu_21_1, pattern='m21_1'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_21_2, pattern='m21_2'))

      dispatcher.add_handler(CallbackQueryHandler(submenu_22_1, pattern='m22_1'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_22_2, pattern='m22_2'))

      dispatcher.add_handler(CallbackQueryHandler(submenu_31, pattern='m3_1'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_32, pattern='m3_2'))

      dispatcher.add_handler(CallbackQueryHandler(submenu_31_1, pattern='m31_1'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_31_11, pattern='m3111'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_31_2, pattern='m31_2'))

      dispatcher.add_handler(CallbackQueryHandler(submenu_32_1, pattern='m32_1'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_32_2, pattern='m32_2'))
      dispatcher.add_handler(CallbackQueryHandler(submenu_32_3, pattern='m32_3'))

      dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=main_menu), -2)

      dispatcher.add_error_handler(error)  

    except Exception as e:
        logging.error(str(e))

def main():

  try:
    # set up logging to standard output
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    updater = Updater(bot_config.api_token, use_context=True)

    message = "⏳*Iniciando...*\n\n_%s %s_\n\n`(%s)`\n\n`(%s)`"%(updater.bot.username, config.version, config.script_name, config.host_name)
    updater.bot.send_message(chat_id=config.admin_telegram_id, text=message, parse_mode=ParseMode.MARKDOWN)    

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    main_commands(dispatcher=dispatcher)

    message = "_%s %s_ *INICIADO* _com sucesso!_ ☑\n`(%s)`\n`(%s)`"%(updater.bot.username, config.version, config.script_name, config.host_name)
    updater.bot.send_message(chat_id=config.admin_telegram_id, text=message, parse_mode=ParseMode.MARKDOWN)     

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    message = "_%s %s_ *PARADO!*\n`(%s)`\n`(%s)`"%(updater.bot.username, config.version, config.script_name, config.host_name)		
    updater.bot.send_message(chat_id=config.admin_telegram_id, text=message, parse_mode=ParseMode.MARKDOWN)     

  except Exception as e:
    logging.error(str(e))   

################################################################################

if __name__ == '__main__':
	main() 