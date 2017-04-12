#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler,ConversationHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from Repository import Repository
from youtrack.connection import Connection
from datetime import datetime
import socket
import urlparse
#Sesiones Activas, sustituir por Memcached
sesiones = {}

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
# Estados
IDENTIFICACION, VER, ELEGIR_ISSUE, HACER_ACTIVIDAD, RECIBIR, CONFIRMAR,ELEGIR_HOST,ELEGIR_PROYECTO = range(8)
# Database
usuarios = Repository('users','ttbot')
#usuarios.getCollection().remove({})
connections = {}

def utf8(unicode_text):
    return unicode_text.encode('utf-8')

def start(bot, update):
    logger.info("Bot Started")
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    # Conocemos al usuario?
    usuario = usuarios.getCollection().find_one({'chat_id':update.message.chat_id})
    if usuario:
        keyboard = []
        for host in usuario['hosts']:
            keyboard.append([InlineKeyboardButton(text=host['host'], callback_data=host['host'])])
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
    	logger.info("{} hosts registrados para el usuario".format(len(keyboard)))
    	update.message.reply_text("Elegí un host para conectarte", reply_markup=reply_markup)
    	return ELEGIR_HOST
    update.message.reply_text("Hola, parece que no estás registrado, por favor mandá el host de youtrack")
    return IDENTIFICACION

def salir(bot, update, user_data):
    logger.info("Salir {}".format(user_data['host']['username']))
    user_data.clear()
    update.message.reply_text("Chau!")
    return ConversationHandler.END

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def checkAndFixUrl(raw_data):
    finalUrl = None
    url = urlparse.urlparse(raw_data)
    if not url.scheme:
        raw_data = 'http://'+raw_data
        url = urlparse.urlparse(raw_data)
    #Ver si resuelve o excepcion
    hostname = socket.gethostbyname(url.hostname)
    if url.path:
        finalUrl = url.scheme+'://'+url.netloc+'/'+url.path
    else:
        finalUrl = url.scheme+'://'+url.netloc
    return finalUrl

def identificar(bot, update, user_data):
    info = update.message.text
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    logger.info("Info received {}".format(info))
    if not user_data.get('host',None) or not user_data['host'].get('host',None):
        try:
            info = checkAndFixUrl(info)
            user_data['host'] = {}
            user_data['host']['host'] = info
            keyboard = [[InlineKeyboardButton(text="Correcto", callback_data='host_ok'),InlineKeyboardButton(text="Corregir", callback_data='host_ko')]]
            reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
            update.message.reply_text("Es correcto el host? {}:".format(user_data['host']['host']), reply_markup=reply_markup)
            return CONFIRMAR
        except Exception as e:
            logger.error(e)
            update.message.reply_text("{} no parece ser un host correcto, intentá de nuevo".format(info))
            return IDENTIFICACION
    elif not user_data['host'].get('username',None):
        user_data['host']['username'] = info
        keyboard = [[InlineKeyboardButton(text="Correcto", callback_data='username_ok'),InlineKeyboardButton(text="Corregir", callback_data='username_ko')]]
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
        update.message.reply_text("Es correcto el usuario? {}:".format(user_data['host']['username']), reply_markup=reply_markup)
        return CONFIRMAR
    else:
        #Try to login
        user_data['host']['pass'] = info
        try:
            connection = Connection(user_data['host']['host'],user_data['host']['username'],user_data['host']['pass'])
            logger.info("good login")
            usuario = usuarios.getCollection().find_one({'chat_id':update.message.chat_id})
            if not usuario:
                usuarios.getCollection().insert_one({'chat_id':update.message.chat_id,'hosts':[user_data['host']]})
            else:
                usuarios.getCollection().update_one({'chat_id':update.message.chat_id},{'$push':{'hosts':user_data['host']}})
            logger.info(user_data['host'])
            proyectos = connection.getProjects()
            keyboard = []
            for proyecto in proyectos.keys():
                keyboard.append([InlineKeyboardButton(proyectos[proyecto],callback_data=proyecto)])
            reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            update.message.reply_text("Bien! Elegí un proyecto"  ,reply_markup=reply_markup)
            return ELEGIR_PROYECTO

        except Exception as e:
            logger.error(e)
            update.message.reply_text("Clave incorrecta")
            return IDENTIFICACION

        return CONFIRMAR

def confirmar_host_ok(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    update.callback_query.edit_message_text(text="Ingresá el nombre de usuario o mail para el login")
    return IDENTIFICACION

def confirmar_host_ko(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    del user_data['host']['host']
    update.callback_query.edit_message_text(text="Ingresá nuevamente el host")
    return IDENTIFICACION

def confirmar_username_ok(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    update.callback_query.edit_message_text(text="Ingresá tu clave para el login")
    return IDENTIFICACION

def confirmar_username_ko(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    del user_data['host']['username']
    update.callback_query.edit_message_text(text="Ingresá nuevamente el usuario")
    return IDENTIFICACION

def elegir_host(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    logger.info('Elegir host Opción {}'.format(update.callback_query.data))

    host = next(x for x in usuario['hosts'] if x['host'] == update.callback_query.data)
    user_data['host'] = host

    connection = Connection(user_data['host']['host'],user_data['host']['username'],user_data['host']['pass'])
    connections[usuario['chat_id']] = connection

    proyectos = connection.getProjects()

    keyboard = []
    for proyecto in proyectos.keys():
        keyboard.append([InlineKeyboardButton(proyectos[proyecto],callback_data=proyecto)])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.callback_query.edit_message_text(text="Bien! Elegí un proyecto"  ,reply_markup=reply_markup)
    return ELEGIR_PROYECTO

def elegir_proyecto(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    user_data['proyecto'] = update.callback_query.data
    logger.info('Elegir Proyecto Opción {}'.format(user_data['proyecto']))

    connection = Connection(user_data['host']['host'],user_data['host']['username'],user_data['host']['pass'])
    issues = connection.getIssues(user_data['proyecto'],'assignee:'+user_data['host']['username'],0,10)

    keyboard = []
    texto = '*Tareas:* \n '
    for issue in issues:
        texto += '\n *[{}]* _{}, {}_\n *Prioridad:* _{}_\n *Resumen:* {} \n\n *Elegí la tarea:*'.format(issue['id'],issue['Type'],issue['State'],issue['Priority'],utf8(issue['summary']))
        keyboard.append([InlineKeyboardButton(issue['id'],callback_data=issue['id'])])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
    logger.info(texto)
    if len(keyboard) > 0:
        update.callback_query.edit_message_text(text=texto,reply_markup=reply_markup,parse_mode='Markdown')
        return ELEGIR_ISSUE
    else:
        update.callback_query.edit_message_text(text="No hay tareas asignadas a vos! Chau")
        return ConversationHandler.END

def elegir_issue(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    user_data['issue'] = update.callback_query.data
    logger.info('Elegir Issue {} Opción {}'.format(user_data['proyecto'],user_data['issue']))

    connection = Connection(user_data['host']['host'],user_data['host']['username'],user_data['host']['pass'])
    the_types = connection.getProjectTimeTrackingWorkTypes(user_data['proyecto'])

    user_data['types'] = the_types['types']
    keyboard = []
    for one_type in the_types['types']:
        keyboard.append([InlineKeyboardButton(one_type['name'],callback_data=one_type['id'])])

    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.callback_query.edit_message_text(text="Elegí el tipo",reply_markup=reply_markup)
    return RECIBIR


def pedir_horas(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    user_data['tipo_id'] = update.callback_query.data
    user_data['tipo_nom'] = next(x['name'] for x in user_data['types'] if x['id'] == user_data['tipo_id'])

    logger.info('Recibir horas {} {} Tipo {}'.format(user_data['proyecto'],user_data['issue'],user_data['tipo_id']))

    update.callback_query.edit_message_text("Envía la cantidad de minutos de {} que hiciste en {}".format(user_data['tipo_nom'],user_data['issue']))
    return RECIBIR

def recibir_horas(bot, update, user_data):

    try:
        duracion = int(update.message.text)
        logger.info(duracion)
    except ValueError:
        logger.error("No entiendo el número!")
        update.message.reply_text("No entiendo el número!")
        return RECIBIR

    work_item = {}
    work_item['duration'] = duracion
    work_item['date'] = str(datetime.now())
    work_item['worktype'] = user_data['tipo_nom']
    work_item['description'] = 'bot :)'
    work_item = dotdict(work_item)
    logger.info(work_item)

    try:
        connection = Connection(user_data['host']['host'],user_data['host']['username'],user_data['host']['pass'])
        connection.createWorkItem(user_data['issue'],work_item)
        logger.info('Guardar tiempo {} {}'.format(user_data['issue'],duracion))
        update.message.reply_text("Gracias amego!")
    except Exception as e :
        logger.error(e)
        update.message.reply_text("No eh!")

    return ConversationHandler.END

def terminar(bot, update):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    logger.info('Elegir ({}) {}'.format(utf8(usuario['nombre']),update.callback_query.data))


    update.callback_query.edit_message_text(text="Hasta la próxima {}!".format(utf8(usuario['nombre'])))

    return ConversationHandler.END

def ver(bot, update):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    logger.info('Elegir ({}) {}'.format(utf8(usuario['nombre']),update.callback_query.data))


    update.callback_query.edit_message_text(text="Actividades de {}!".format(utf8(usuario['nombre'])))

    return VER

def registrar(bot, update, args):
    update.message.reply_text("Gracias! %" % args)

class dotdict(dict):
     """dot.notation access to dictionary attributes"""
     __getattr__ = dict.get
     __setattr__ = dict.__setitem__
     __delattr__ = dict.__delitem__
