#!/usr/bin/env python3.7

# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
# type: ignore[union-attr]

"""
Modelo de bot genérico.

Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Atualizador de recebimento de mensagens
updater:Updater = None

# Bot users internal cache
users_cache = {}

# Todos os usuários, autorizados ou não:
not_allowed_users_cache = {}

# armazena o job global periódico
job_minute = None
job_ping = None