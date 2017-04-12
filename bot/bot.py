#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler,ConversationHandler,RegexHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from bot_utils import start,identificar,error,elegir_proyecto,elegir_issue,recibir_horas,terminar,confirmar_host_ok,confirmar_host_ko,confirmar_username_ok,confirmar_username_ko,elegir_host,pedir_horas,salir
from bot_utils import IDENTIFICACION, ELEGIR_ISSUE, HACER_ACTIVIDAD, RECIBIR, VER,CONFIRMAR,ELEGIR_HOST,ELEGIR_PROYECTO

keys = {}
exec(open('key_all.py').read(), keys)
updater = Updater(token=keys['telegram'])


dispatcher = updater.dispatcher
conv_handler = ConversationHandler(
	entry_points=[CommandHandler('start', start)],
    states={
        IDENTIFICACION: [MessageHandler(Filters.text, identificar, pass_user_data=True)],
		CONFIRMAR: [
			CallbackQueryHandler(confirmar_host_ok,pattern='.*host_ok.*',pass_user_data=True),
			CallbackQueryHandler(confirmar_host_ko,pattern='.*host_ko.*',pass_user_data=True),
			CallbackQueryHandler(confirmar_username_ok,pattern='.*username_ok.*',pass_user_data=True),
			CallbackQueryHandler(confirmar_username_ko,pattern='.*username_ko.*',pass_user_data=True)
		],
		ELEGIR_HOST:[CallbackQueryHandler(elegir_host,pass_user_data=True)],
		ELEGIR_PROYECTO:[CallbackQueryHandler(elegir_proyecto,pass_user_data=True)],
	    ELEGIR_ISSUE: [CallbackQueryHandler(elegir_issue,pass_user_data=True)],
        HACER_ACTIVIDAD: [],

        RECIBIR: [CallbackQueryHandler(pedir_horas, pass_user_data=True),MessageHandler(Filters.text, recibir_horas, pass_user_data=True)],
        },
    fallbacks=[CommandHandler('salir', salir, pass_user_data=True)]
    )
dispatcher.add_handler(conv_handler)




# log all errors
dispatcher.add_error_handler(error)

#Con SSL
#updater.start_webhook(listen="127.0.0.1",port=8443,url_path=keys['telegram'])
#updater.bot.setWebhook("https://tt-bot.mgcoders.com/" + keys['telegram'])
#POLLING
updater.start_polling()
updater.idle()
