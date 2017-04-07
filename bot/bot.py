#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler,ConversationHandler,RegexHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from libs.bot_utils import start,contact,error,elegir_rutina,elegir_dia,elegir_ejercicio,registrar,opciones,acerca_de,terminar,ver, hacer_ejercicio
from libs.bot_utils import IDENTIFICACION, OPCIONES, ELEGIR_ACTIVIDAD, HACER_ACTIVIDAD, REGISTRAR, VER

keys = {}
exec(open('libs/key_all.py').read(), keys)
updater = Updater(token=keys['telegram'])


dispatcher = updater.dispatcher

conv_handler = ConversationHandler(
	entry_points=[CommandHandler('start', start)],
        states={
            IDENTIFICACION: [MessageHandler(Filters.contact, contact)],
            OPCIONES: [CallbackQueryHandler(opciones,pattern='.*seguir.*'),CallbackQueryHandler(acerca_de,pattern='.*acerca_de.*')],
	    ELEGIR_ACTIVIDAD: [
				CallbackQueryHandler(elegir_ejercicio,pattern='.*dia.*'),
				CallbackQueryHandler(elegir_dia,pattern='.*rutina.*'),
				CallbackQueryHandler(elegir_rutina,pattern='.*entrenar.*'),
				CallbackQueryHandler(ver,pattern='.*ver.*')
				],
            HACER_ACTIVIDAD: [
				CallbackQueryHandler(hacer_ejercicio)
				],
				VER: [],
            REGISTRAR: [MessageHandler(Filters.text, registrar, pass_user_data=True)],
        },
        fallbacks=[CallbackQueryHandler(terminar,pattern='.*terminar.*')]
    )
dispatcher.add_handler(conv_handler)




# log all errors
dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()





