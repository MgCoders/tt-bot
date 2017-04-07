#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler,ConversationHandler,RegexHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from libs.bot_utils import start,contact,error,elegir_rutina,elegir_dia,elegir_ejercicio,registrar,opciones,acerca_de,terminar,ver, hacer_ejercicio, actualizar_peso
from libs.bot_utils import IDENTIFICACION, OPCIONES, ELEGIR_ACTIVIDAD, HACER_ACTIVIDAD, RECIBIR, VER

keys = {}
exec(open('libs/key_all.py').read(), keys)
updater = Updater(token=keys['telegram'])


dispatcher = updater.dispatcher
conv_handler = ConversationHandler(
	entry_points=[CommandHandler('start', start)],
    states={
        IDENTIFICACION: [MessageHandler(Filters.contact, contact)],
        OPCIONES: [
			CallbackQueryHandler(opciones,pattern='.*seguir.*',pass_user_data=True),
			CallbackQueryHandler(acerca_de,pattern='.*acerca_de.*',pass_user_data=True)],
	    ELEGIR_ACTIVIDAD: [
				CallbackQueryHandler(elegir_ejercicio,pattern='.*dia.*',pass_user_data=True),
				CallbackQueryHandler(elegir_dia,pattern='.*rutina.*',pass_user_data=True),
				CallbackQueryHandler(elegir_rutina,pattern='.*entrenar.*',pass_user_data=True),
				CallbackQueryHandler(ver,pattern='.*ver.*',pass_user_data=True)
				],
        HACER_ACTIVIDAD: [
				CallbackQueryHandler(hacer_ejercicio,pass_user_data=True)
				],
		VER: [],
        RECIBIR: [MessageHandler(Filters.text, actualizar_peso, pass_user_data=True)],
        },
    fallbacks=[CallbackQueryHandler(terminar,pattern='.*terminar.*')]
    )
dispatcher.add_handler(conv_handler)




# log all errors
dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()
