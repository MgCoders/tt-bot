#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, ConversationHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from Repository import Repository
from youtrack.connection import Connection
from youtrack import YouTrackException
from datetime import datetime
from utils import utf8, escapeMarkdown, checkAndFixUrl, splitEmail

# Sesiones Activas, sustituir por Memcached
sesiones = {}

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
# Estados
IDENTIFICAR, VER, ISSUE, HACER_ACTIVIDAD, RECIBIR, CONFIRMAR, HOST, PROYECTO = range(8)
# Database
usuarios = Repository('users', 'ttbot')
# usuarios.getCollection().remove({})
connections = {}


def start(bot, update):
    logger.info("Bot Started")
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    # Conocemos al usuario?
    usuario = usuarios.getCollection().find_one({'chat_id': update.message.chat_id})
    if usuario:
        keyboard = []
        for host in usuario['hosts']:
            keyboard.append([InlineKeyboardButton(text=host['host'], callback_data=host['host'])])
        keyboard.append([InlineKeyboardButton(text='Agregar nuevo host', callback_data='nuevo_host')])
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
        logger.info("{} hosts registrados para el usuario".format(len(usuario['hosts'])))
        update.message.reply_text("Elegí un host para conectarte", reply_markup=reply_markup)
        return HOST
    update.message.reply_text("Hola, parece que no estás registrado, por favor mandá el host de youtrack")
    return IDENTIFICAR


def salir(bot, update, user_data):
    if user_data.get('host'):
        logger.info("Salir {}".format(user_data['host']['username']))
    else:
        logger.info("Salir invitado")
    user_data.clear()
    update.message.reply_text("Chau!")
    return ConversationHandler.END


def error(bot, update, user_data):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
    if user_data.get('host'):
        logger.info("Salir Error {}".format(user_data['host']['username']))
    else:
        logger.info("Salir Error invitado")
    user_data.clear()
    update.message.reply_text("Hubo un error Chau!")
    return ConversationHandler.END


def nuevo_host(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    update.callback_query.edit_message_text(text="Ingresá el host")
    return IDENTIFICAR


def identificar(bot, update, user_data):
    info = update.message.text
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    if not user_data.get('host', None) or not user_data['host'].get('host', None):
        logger.info("Host received {}".format(info))
        try:
            info = checkAndFixUrl(info)
            user_data['host'] = {}
            user_data['host']['host'] = info
            keyboard = [[InlineKeyboardButton(text="Correcto", callback_data='host_ok'),
                         InlineKeyboardButton(text="Corregir", callback_data='host_ko')]]
            reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
            update.message.reply_text("Es correcto el host? {}:".format(user_data['host']['host']),
                                      reply_markup=reply_markup)
            return CONFIRMAR
        except Exception as e:
            logger.error(e)
            update.message.reply_text("{} no parece ser un host correcto, intentá de nuevo".format(info))
            return IDENTIFICAR
    elif not user_data['host'].get('username', None):
        logger.info("Username received {}".format(info))
        user_data['host']['username'] = info
        keyboard = [[InlineKeyboardButton(text="Correcto", callback_data='username_ok'),
                     InlineKeyboardButton(text="Corregir", callback_data='username_ko')]]
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
        update.message.reply_text("Es correcto el usuario? {}:".format(user_data['host']['username']),
                                  reply_markup=reply_markup)
        return CONFIRMAR
    else:
        logger.info("Password received")
        # Try to login
        user_data['host']['pass'] = info
        try:
            connection = Connection(user_data['host']['host'], user_data['host']['username'], user_data['host']['pass'])
            logger.info("good login")
            usuario = usuarios.getCollection().find_one({'chat_id': update.message.chat_id})
            if not usuario:
                usuarios.getCollection().insert_one({'chat_id': update.message.chat_id, 'hosts': [user_data['host']]})
            else:
                usuarios.getCollection().update_one({'chat_id': update.message.chat_id},
                                                    {'$push': {'hosts': user_data['host']}})
            logger.info(user_data['host'])
            proyectos = connection.getProjects()
            keyboard = []
            for proyecto in proyectos.keys():
                keyboard.append([InlineKeyboardButton(proyectos[proyecto], callback_data=proyecto)])
            reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            update.message.reply_text("Bien! Elegí un proyecto", reply_markup=reply_markup)
            return PROYECTO

        except Exception as e:
            logger.error(e)
            update.message.reply_text("Clave incorrecta")
            return IDENTIFICAR

        return CONFIRMAR


def confirmar_host_ok(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    update.callback_query.edit_message_text(text="Ingresá el nombre de usuario o mail para el login")
    return IDENTIFICAR


def confirmar_host_ko(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    del user_data['host']['host']
    update.callback_query.edit_message_text(text="Ingresá nuevamente el host")
    return IDENTIFICAR


def confirmar_username_ok(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    update.callback_query.edit_message_text(text="Ingresá tu clave para el login")
    return IDENTIFICAR


def confirmar_username_ko(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    del user_data['host']['username']
    update.callback_query.edit_message_text(text="Ingresá nuevamente el usuario")
    return IDENTIFICAR


def host_elegido(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    usuario = usuarios.getCollection().find_one({'chat_id': update.callback_query.from_user.id})
    logger.info('Elegir host Opción {}'.format(update.callback_query.data))

    host = next(x for x in usuario['hosts'] if x['host'] == update.callback_query.data)
    user_data['host'] = host

    try:
        connection = Connection(user_data['host']['host'], user_data['host']['username'], user_data['host']['pass'])
        connections[usuario['chat_id']] = connection
        proyectos = connection.getProjects()

    except YouTrackException as e:
        logger.error(e)
        del user_data['host']['pass']
        usuarios.getCollection().update({'chat_id': update.callback_query.from_user.id},
                            { '$pull': {'hosts': user_data['host']} });

        return CONFIRMAR




    keyboard = []
    for proyecto in proyectos.keys():
        keyboard.append(InlineKeyboardButton(proyectos[proyecto], callback_data=proyecto))

    # Acomodo el teclado
    keyboard = [keyboard[i:i + 3] for i in range(0, len(keyboard), 3)]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.callback_query.edit_message_text(text="Bien! Elegí un proyecto", reply_markup=reply_markup)
    return PROYECTO


def proyecto_elegido(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    # Es la primera vez que entra o cambia tipo de tareas?
    user_data['tipo_tarea'] = '#Unresolved'
    if not user_data.get('proyecto'):
        user_data['proyecto'] = update.callback_query.data
        logger.info('Elegir Proyecto Opción {}'.format(user_data['proyecto']))
    else:
        user_data['tipo_tarea'] = update.callback_query.data
        logger.info('Elegir Proyecto Opción {} {}'.format(user_data['proyecto'], user_data['tipo_tarea']))

    connection = Connection(user_data['host']['host'], user_data['host']['username'], user_data['host']['pass'])
    username, email = splitEmail(user_data['host']['username'])

    query = 'Type: Task and {} and ( Assignee: {} or #Unassigned )'.format(user_data['tipo_tarea'], username)
    issues = connection.getIssues(user_data['proyecto'], query, 0, 20)

    keyboard = []
    texto = '*Tareas:* \n '
    for issue in issues:
        texto += '\n *[{}]* _{}, {}_\n *Prioridad:* _{}_\n *Resumen:* {} \n'.format(issue['id'], issue['Type'],
                                                                                    issue['State'], issue['Priority'],
                                                                                    escapeMarkdown(
                                                                                        utf8(issue['summary'])))
        keyboard.append(InlineKeyboardButton(issue['id'], callback_data=issue['id']))
    # Agrego posibilidad de ver otras tareas
    if user_data['tipo_tarea'] == '#Unresolved':
        keyboard.append(InlineKeyboardButton('Ver solucionadas', callback_data='#Resolved'))
    else:
        keyboard.append(InlineKeyboardButton('Ver no solucionadas', callback_data='#Unresolved'))
    # Acomodo el teclado
    keyboard = [keyboard[i:i + 3] for i in range(0, len(keyboard), 3)]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    texto += '\n *Elegí la tarea:*'

    if len(keyboard) > 0:
        update.callback_query.edit_message_text(text=texto, reply_markup=reply_markup, parse_mode='Markdown')
        return ISSUE
    else:
        update.callback_query.edit_message_text(text="No hay tareas asignadas a vos! Chau")
        return ConversationHandler.END


def issue_elegido(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    user_data['issue'] = update.callback_query.data
    logger.info('Elegir Issue {} Opción {}'.format(user_data['proyecto'], user_data['issue']))

    connection = Connection(user_data['host']['host'], user_data['host']['username'], user_data['host']['pass'])
    try:
        the_types = connection.getProjectTimeTrackingWorkTypes(user_data['proyecto'])
    except YouTrackException as e:
        logger.error('Error de Youtrack {}'.format(e))
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Elegir otro proyecto", callback_data=user_data['host']['host'])]],
            resize_keyboard=True, one_time_keyboard=True)
        del user_data['proyecto']
        update.callback_query.edit_message_text(text="El proyecto no admite registro de horas, hablá con tu PM",
                                                reply_markup=reply_markup)
        return HOST

    user_data['types'] = the_types['types']
    keyboard = []
    for one_type in the_types['types']:
        keyboard.append([InlineKeyboardButton(one_type['name'], callback_data=one_type['id'])])

    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.callback_query.edit_message_text(text="Elegí el tipo", reply_markup=reply_markup)
    return RECIBIR


def pedir_horas(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    user_data['tipo_id'] = update.callback_query.data
    user_data['tipo_nom'] = next(x['name'] for x in user_data['types'] if x['id'] == user_data['tipo_id'])

    logger.info('Recibir horas {} {} Tipo {}'.format(user_data['proyecto'], user_data['issue'], user_data['tipo_id']))

    update.callback_query.edit_message_text(
        "Envía la cantidad de minutos de {} que hiciste en {}".format(user_data['tipo_nom'], user_data['issue']))
    return RECIBIR


def recibir_horas(bot, update, user_data):
    try:
        duracion = int(update.message.text)
        logger.info(duracion)
    except ValueError:
        logger.error("No entiendo el número!")
        update.message.reply_text("No entiendo el número!")
        return RECIBIR

    work_item = {'duration': duracion, 'date': str(datetime.now()), 'worktype': user_data['tipo_nom'],
                 'description': 'bot :)'}
    work_item = dotdict(work_item)
    logger.info(work_item)

    try:
        connection = Connection(user_data['host']['host'], user_data['host']['username'], user_data['host']['pass'])
        connection.createWorkItem(user_data['issue'], work_item)
        logger.info('Guardar tiempo {} {}'.format(user_data['issue'], duracion))

        issue = connection.getIssue(user_data['issue'])

        keyboard = []
        if user_data['tipo_tarea'] == '#Unresolved':
            keyboard.append([InlineKeyboardButton('Marcar como cerrada', callback_data='issue_estado_cerrar')])
        else:
            keyboard.append([InlineKeyboardButton('Marcar como en progreso', callback_data='issue_estado_en_progreso')])
        keyboard.append([InlineKeyboardButton('Dejar como {}'.format(issue['State']),
                                              callback_data='terminar')])
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text("Gracias amego! Y ahora?", reply_markup=reply_markup)
        return CONFIRMAR

    except Exception as e:
        logger.error(e)
        update.message.reply_text("No eh!")

    return ConversationHandler.END


def issue_actualizar_estado(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    if update.callback_query.data == 'issue_estado_cerrar':
        estado = 'Fixed'
    else:
        estado = 'In Progress'

    logger.info('Actualizar estado issue {} {}'.format(user_data['issue'], estado))
    try:
        connection = Connection(user_data['host']['host'], user_data['host']['username'], user_data['host']['pass'])
        command = 'State '+estado
        connection.executeCommand(user_data['issue'], command)

        update.callback_query.edit_message_text("Gracias amego!")

    except Exception as e:
        logger.error(e)
        update.callback_query.edit_message_text("No eh!")
    return ConversationHandler.END


def terminar(bot, update,user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id': update.callback_query.from_user.id})
    logger.info('Terminar ({})'.format(user_data['host']['username']))

    update.callback_query.edit_message_text(text="Hasta la próxima!")
    user_data.clear()
    return ConversationHandler.END


def ver(bot, update):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id': update.callback_query.from_user.id})
    logger.info('Elegir ({}) {}'.format(utf8(usuario['nombre']), update.callback_query.data))

    update.callback_query.edit_message_text(text="Actividades de {}!".format(utf8(usuario['nombre'])))

    return VER


def registrar(bot, update, args):
    update.message.reply_text("Gracias! %" % args)


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
