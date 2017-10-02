#!/bin/python
# -*- coding: utf-8 -*-

import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler, \
    ConversationHandler, RegexHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from bot_utils import start, identificar, error, proyecto_elegido, issue_elegido, recibir_horas, terminar, \
    confirmar_host_ok, confirmar_host_ko, confirmar_username_ok, confirmar_username_ko, host_elegido, pedir_horas, \
    salir, issue_actualizar_estado, nuevo_host
from bot_utils import IDENTIFICAR, ISSUE, RECIBIR, CONFIRMAR, HOST, \
    PROYECTO

logger = logging.getLogger(__name__)
keys = {}
keys['telegram'] = os.getenv('TOKEN', 'token')
updater = Updater(token=keys['telegram'])

dispatcher = updater.dispatcher
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        IDENTIFICAR: [MessageHandler(Filters.text, identificar, pass_user_data=True)],
        CONFIRMAR: [
            CallbackQueryHandler(confirmar_host_ok, pattern='.*host_ok.*', pass_user_data=True),
            CallbackQueryHandler(confirmar_host_ko, pattern='.*host_ko.*', pass_user_data=True),
            CallbackQueryHandler(confirmar_username_ok, pattern='.*username_ok.*', pass_user_data=True),
            CallbackQueryHandler(confirmar_username_ko, pattern='.*username_ko.*', pass_user_data=True),
            CallbackQueryHandler(issue_actualizar_estado, pattern='.*issue_estado.*', pass_user_data=True)
        ],
        HOST: [CallbackQueryHandler(nuevo_host, pattern='.*nuevo_host.*', pass_user_data=True),
               CallbackQueryHandler(host_elegido, pass_user_data=True)],
        PROYECTO: [CallbackQueryHandler(proyecto_elegido, pass_user_data=True)],
        ISSUE: [CallbackQueryHandler(proyecto_elegido, pattern='.*esolved.*', pass_user_data=True),
                CallbackQueryHandler(issue_elegido, pass_user_data=True)],
        RECIBIR: [CallbackQueryHandler(pedir_horas, pass_user_data=True),
                  MessageHandler(Filters.text, recibir_horas, pass_user_data=True)]
    },
    fallbacks=[CommandHandler('salir', salir, pass_user_data=True), CallbackQueryHandler(terminar, pattern='terminar', pass_user_data=True)]
)
dispatcher.add_handler(conv_handler)

# log all errors
dispatcher.add_error_handler(error)

mode = os.getenv('MODE', 'polling')
logger.info("Will run in %s mode.",mode)
if mode == 'webhook':
    # Con SSL
    updater.start_webhook(listen="0.0.0.0",port=8443,url_path=keys['telegram'])
    updater.bot.setWebhook("https://"+os.getenv('VIRTUAL_HOST', 'localhost')+"/" + keys['telegram'])
    logger.info("Listening in %s .","https://"+os.getenv('VIRTUAL_HOST', 'localhost')+"/TOKEN")
    updater.idle()
else:
    # POLLING
    updater.start_polling()
    logger.info("Polling...")
    updater.idle()
