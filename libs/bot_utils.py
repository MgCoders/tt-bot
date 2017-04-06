#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler,ConversationHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from libs.Repository import Repository

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
# Estados
IDENTIFICACION, OPCIONES, ELEGIR_RUTINA, ELEGIR_ACTIVIDAD, REGISTRAR = range(5)
# Database
usuarios = Repository('usuarios','gymbot')
rutinas = Repository('rutinas','gymbot')  

def utf8(unicode_text):
    return unicode_text.encode('utf-8')

def start(bot, update):
    logger.info("Bot Started")
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    # Conocemos al usuario?
    usuario = usuarios.getCollection().find_one({'chat_id':update.message.chat_id})
    if usuario:
        keyboard = [[InlineKeyboardButton(text="Claro!", callback_data='1'),InlineKeyboardButton(text="Eh? ¿Esto que es?", callback_data='2')]]
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
    	logger.info("Usuario conocido %s" % usuario['nombre'])
    	update.message.reply_text("¿Estás list@ %s?" % utf8(usuario['nombre']), reply_markup=reply_markup)
    	return OPCIONES
    keyboard = [[KeyboardButton(text="Enviar número", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text("¿Estás de acuerdo en enviarnos tu número para continuar?", reply_markup=reply_markup)
    return IDENTIFICACION
 
def opciones(bot,update):
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    logger.info('Opciones ({}), Opción {}'.format(utf8(usuario['nombre']),update.callback_query.data))
    keyboard = [
        [InlineKeyboardButton(text="Entrenar", callback_data='opcion_entrenar'),InlineKeyboardButton(text="Ver", callback_data='opcion_ver')],
        [InlineKeyboardButton(text="Nada", callback_data='opcion_nada')]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
    
    update.callback_query.answer("Siempre listo!")
    update.callback_query.edit_message_text(text="¿Que querés hacer?", reply_markup=reply_markup)

    return ELEGIR_ACTIVIDAD
    

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
                        
def contact(bot, update):
    user = update.message.from_user
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    logger.info("Contact received from %s" % user.first_name)
    logger.info("Phone number %s" % update.message.contact.phone_number)
    # Conocemos al usuario?
    usuario = usuarios.getCollection().find_one({'numero':update.message.contact.phone_number})
    if usuario:
        entrenador = usuarios.getCollection().find_one({'numero':usuario['entrenador']})
        logger.info("Guardamos chat_id del usuario %s" % update.message.chat_id)
        usuarios.update_one(str(usuario['_id']),'chat_id',update.message.chat_id)
        usuarios.update_one(str(usuario['_id']),'nombre',user.first_name)
    	update.message.reply_text("Entrenamos? Elegi una rutina, El profesor %s te sugiere:" % utf8(entrenador['nombre']), reply_markup=reply_markup)
    	return ELEGIR
    else:
        update.message.reply_text("Necesitás ser invitado por tu entrenador, nos vemos!",reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
    
def elegir_rutina(bot, update):
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    logger.info('Elegir ({}), Opción {}'.format(utf8(usuario['nombre']),update.callback_query.data))
    
    entrenador = usuarios.getCollection().find_one({'numero':usuario['entrenador']})
    rutinas_usuario = rutinas.find({'entrenador':entrenador['numero']})
    
    keyboard = []
    for rutina in rutinas_usuario:
        keyboard.append([InlineKeyboardButton(rutina['descripcion'],callback_data=str({'rutina':rutina['nombre']}))])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.callback_query.answer("Bien! Entrenemos")
    update.callback_query.edit_message_text(text="%s preparó ejercicios para vos, elegí:" % utf8(entrenador['nombre']), 
        reply_markup=reply_markup)
    return ELEGIR_ACTIVIDAD    

def elegir_dia(bot, update):
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    callback_data = eval(update.callback_query.data)
    logger.info('Elegir ({}), Rutina {}'.format(utf8(usuario['nombre']),callback_data['rutina']))
    
    rutina = rutinas.getCollection().find_one({'nombre':callback_data['rutina']})
    
    keyboard = []
    for dia in rutina['dia']:
        callback_data['dia'] = dia['nombre']
        keyboard.append([InlineKeyboardButton(dia['nombre'],callback_data=str(callback_data))])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.callback_query.answer("Excelente! %s" % callback_data['rutina'])
    update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
   
    return ELEGIR_ACTIVIDAD  

def elegir_ejercicio(bot, update):
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    callback_data = eval(update.callback_query.data)
    logger.info('Elegir ({}), Rutina {}, Día {}'.format(utf8(usuario['nombre']),callback_data['rutina'],callback_data['dia']))
    
    rutina = rutinas.getCollection().find_one({'nombre':callback_data['rutina']})
    dia = next(x for x in rutina['dia'] if x['nombre'] == callback_data['dia'])

    keyboard = []
    for ejercicio in dia['ejercicio']:
        callback_data['ejercicio'] = 'un'#ejercicio['nombre']
        keyboard.append([InlineKeyboardButton(ejercicio['nombre'],callback_data=str(callback_data))])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.callback_query.answer("Vamos con %s!" % callback_data['dia'])
    update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)

    return ELEGIR_ACTIVIDAD     
    
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
    

