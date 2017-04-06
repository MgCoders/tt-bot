#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler,ConversationHandler,RegexHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from libs.bot_utils import start,contact,error,elegir_rutina,elegir_dia,elegir_ejercicio,registrar,done,opciones
from libs.bot_utils import IDENTIFICACION, OPCIONES, ELEGIR_ACTIVIDAD, REGISTRAR

keys = {}
exec(open('libs/key_all.py').read(), keys)
updater = Updater(token=keys['telegram'])


dispatcher = updater.dispatcher

conv_handler = ConversationHandler(
	entry_points=[CommandHandler('start', start)],
        states={
            IDENTIFICACION: [MessageHandler(Filters.contact, contact)],
            OPCIONES: [CallbackQueryHandler(opciones)],
	    ELEGIR_ACTIVIDAD: [
				CallbackQueryHandler(elegir_ejercicio,pattern='.*dia.*'),
				CallbackQueryHandler(elegir_dia,pattern='.*rutina.*'),
				CallbackQueryHandler(elegir_rutina,pattern='.*opcion_entrenar.*')
				],
            REGISTRAR: [MessageHandler(Filters.text, registrar, pass_user_data=True)],
        },
        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    )
dispatcher.add_handler(conv_handler)




# log all errors
dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()





