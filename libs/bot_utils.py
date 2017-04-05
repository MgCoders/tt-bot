#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from libs.Repository import Repository

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
# Estados
IDENTIFICACION, ELEGIR, REGISTRAR = range(3)
# Database
usuarios = Repository('usuarios','gymbot')
rutinas = Repository('rutinas','gymbot')  

def start(bot, update):
    keyboard = [[KeyboardButton(text="Enviar número", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    logger.info("Bot Started")
    # Conocemos al usuario?
    usuario = usuarios.getCollection().find_one({'chat_id':update.message.chat_id})
    if usuario:
    	logger.info("Usuario conocido %s" % usuario['nombre'])
    	update.message.reply_text("Te conocemos man!")
    	return ELEGIR
    update.message.reply_text("¿Estás de acuerdo en enviarnos tu número para continuar?", reply_markup=reply_markup)
    return IDENTIFICACION
 

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
                        
def contact(bot, update):
    user = update.message.from_user
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    logger.info("Contact received from %s" % user.first_name)
    logger.info("Phone number %s" % update.message.contact.phone_number)
    # Conocemos al usuario?
    usuario = usuarios.getCollection().find_one({'numero':update.message.contact.phone_number})
    entrenador = usuarios.getCollection().find_one({'numero':usuario['entrenador']})
    if usuario:
        logger.info("Guardamos chat_id del usuario %s" % update.message.chat_id)
        usuarios.update_one(str(usuario['_id']),'chat_id',update.message.chat_id)
        rutinas_usuario = rutinas.find({'entrenador':entrenador['numero']})
        keyboard = []
        for rutina in rutinas_usuario:
        	keyboard.append([InlineKeyboardButton(rutina['descripcion'])])
    	reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    	update.message.reply_text("Entrenamos? Elegi una rutina, El profesor %s te sugiere:" % entrenador['nombre'], reply_markup=reply_markup)
    	return ELEGIR
    else:
        update.message.reply_text("Necesitás ser invitado por tu entrenador, nos vemos!")
    return ConversationHandler.END
    
def elegir(bot, update , user_data):
    logger.info("Elegir")
    update.message.reply_text("Gracias!")
    
def registrar(bot, update, args):
    update.message.reply_text("Gracias! %" % args)

def done(bot, update, user_data):
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text("I learned these facts about you:"
                              "%s"
                              "Until next time!" % facts_to_str(user_data))

    user_data.clear()
    return ConversationHandler.END
    

