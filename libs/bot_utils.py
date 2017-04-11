#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler,ConversationHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from Repository import Repository
from youtrack.connection import Connection


#Sesiones Activas, sustituir por Memcached
sesiones = {}

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
# Estados
IDENTIFICACION, VER, ELEGIR_ISSUE, HACER_ACTIVIDAD, RECIBIR, CONFIRMAR,ELEGIR_HOST,ELEGIR_PROYECTO = range(8)
# Database
usuarios = Repository('users','ttbot')
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

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def identificar(bot, update, user_data):
    info = update.message.text
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    logger.info("Info received {}".format(info))
    if not user_data.get('host',None):
        user_data['host'] = info
        keyboard = [[InlineKeyboardButton(text="Correcto", callback_data='host_ok'),InlineKeyboardButton(text="Corregir", callback_data='host_ko')]]
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
        update.message.reply_text("Es correcto el host? {}:".format(user_data['host']), reply_markup=reply_markup)
        return CONFIRMAR
    elif not user_data.get('username',None):
        user_data['username'] = info
        keyboard = [[InlineKeyboardButton(text="Correcto", callback_data='username_ok'),InlineKeyboardButton(text="Corregir", callback_data='username_ko')]]
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
        update.message.reply_text("Es correcto el usuario? {}:".format(user_data['username']), reply_markup=reply_markup)
        return CONFIRMAR
    else:
        #Try to login
        user_data['pass'] = info
        try:
            connection = youtrack.Connection(user_data['host'],user_data['username'],user_data['pass'])
            logger.info("good login")
            usuario = usuarios.getCollection().find_one({'chat_id':update.message.chat_id})
            if not usuario:
                usuarios.getCollection().insert_one({'chat_id':update.message.chat_id,'hosts':[user_data]})
            else:
                usuarios.getCollection().update_one({'chat_id':update.message.chat_id},{'$push':{'hosts':user_data}})

        except:
            logger.info("bad")

        return CONFIRMAR

def confirmar_host_ok(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    update.callback_query.edit_message_text(text="Ingresá el nombre de usuario o mail para el login")
    return IDENTIFICACION

def confirmar_host_ko(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    del user_data['host']
    update.callback_query.edit_message_text(text="Ingresá nuevamente el host")
    return IDENTIFICACION

def confirmar_username_ok(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    update.callback_query.edit_message_text(text="Ingresá tu clave para el login")
    return IDENTIFICACION

def confirmar_username_ko(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    del user_data['username']
    update.callback_query.edit_message_text(text="Ingresá nuevamente el usuario")
    return IDENTIFICACION

def elegir_host(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    logger.info('Elegir host Opción {}'.format(update.callback_query.data))

    host = next(x for x in usuario['hosts'] if x['host'] == update.callback_query.data)
    user_data['host'] = host

    connection = Connection(user_data['host']['host'],user_data['host']['username'],user_data['host']['pass'])

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
    logger.info(user_data)

    connection = Connection(user_data['host']['host'],user_data['host']['username'],user_data['host']['pass'])
    issues = connection.getIssues(user_data['proyecto'],'',0,10)

    keyboard = []
    for issue in issues:
        keyboard.append([InlineKeyboardButton(issue['summary'],callback_data=issue['id'])])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.callback_query.edit_message_text(text="Elegí la tarea",reply_markup=reply_markup)
    return ELEGIR_ISSUE

def elegir_issue(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    user_data['issue'] = update.callback_query.data
    logger.info('Elegir Issue {} Opción {}'.format(user_data['proyecto'],user_data['issue']))
    logger.info(user_data)

    connection = Connection(user_data['host']['host'],user_data['host']['username'],user_data['host']['pass'])
    settings = connection.getProjectTimeTrackingWorkTypes()

    logger.info(settings)

    keyboard = [
        [InlineKeyboardButton('Desarrollo',callback_data='Desarrollo')],
        [InlineKeyboardButton('Pruebas',callback_data='Pruebas')],
        [InlineKeyboardButton('Decumentacion',callback_data='Pruebas')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.callback_query.edit_message_text(text="Elegí la tarea",reply_markup=reply_markup)
    return ELEGIR_ISSUE

def elegir_ejercicio(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    usuario = user_data['usuario']
    user_data['dia'] = update.callback_query.data
    logger.info('Elegir ({}), Rutina {}, Día {}'.format(utf8(user_data['usuario']['nombre']),user_data['rutina'],user_data['dia']))

    rutina = rutinas.getCollection().find_one({'nombre':user_data['rutina']})
    dia = next(x for x in rutina['dia'] if x['nombre'] == user_data['dia'])

    keyboard = []
    for ejercicio in dia['ejercicio']:
        keyboard.append([InlineKeyboardButton(ejercicio['nombre'],callback_data=ejercicio['nombre'])])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


    update.callback_query.answer("Vamos con {}!".format(user_data['dia']))
    update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)

    return HACER_ACTIVIDAD

def hacer_ejercicio(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    usuario = user_data['usuario']
    user_data['ejercicio'] = update.callback_query.data
    logger.info('Hacer ({}), Rutina {}, Día {}, Ejercicio {}'.format(utf8(user_data['usuario']['nombre']),user_data['rutina'],user_data['dia'],user_data['ejercicio']))

    #logger.info(user_data)
    rutina = rutinas.getCollection().find_one({'nombre':user_data['rutina']})
    dia = next(x for x in rutina['dia'] if x['nombre'] == user_data['dia'])
    ejercicio = next(x for x in dia['ejercicio'] if x['nombre'] == user_data['ejercicio'])

    #Texto
    if (ejercicio['peso_max']):
    	text = "{} consiste en {} series con cargas relativas a tu peso máximo.".format(utf8(user_data['ejercicio']),len(ejercicio['serie']))
        peso_max_usuario = next((x for x in usuario['pesos_maximos'] if x.get(user_data['ejercicio'],None)),None)
        if not peso_max_usuario:
            peso_max_usuario = -1
            text += " Por favor actualizá tu peso máximo."
    else:
        text = "{} consiste en {} series.".format(utf8(user_data['ejercicio']),len(ejercicio['serie']))


    keyboard = []

    #Seguimos adelante
    if (not peso_max_usuario) or (peso_max_usuario and peso_max_usuario > 0):
        keyboard.append([InlineKeyboardButton('Comenzar',callback_data='comenzar')])
        keyboard.append([InlineKeyboardButton('Cambiar',callback_data='cambiar')])
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
        update.callback_query.answer(user_data['ejercicio'])
        update.callback_query.edit_message_text(text=text,reply_markup=reply_markup)
        #Imágen
        if ejercicio.get('imagen',None):
                data = rutinas.getFs().get(ejercicio['imagen'])
                if data:
                    f = open(data.filename, 'wb')
                    f.write(data.read())
                    f.close()
                    bot.sendPhoto(chat_id=update.callback_query.from_user.id, photo=open(utf8(data.filename), 'rb'))
        return HACER_ACTIVIDAD
    #Actualizar Peso
    else:
        keyboard.append(
            [InlineKeyboardButton('Actualizar Peso Máximo',callback_data='actualizar_peso')]
        )

        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
        update.callback_query.answer(user_data['ejercicio'])
        update.callback_query.edit_message_text(text=text,reply_markup=reply_markup)
        return RECIBIR

def comenzar_ejercicio(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    usuario = user_data['usuario']
    logger.info('Comenzar ({}), Rutina {}, Día {}, Ejercicio {}'.format(utf8(user_data['usuario']['nombre']),user_data['rutina'],user_data['dia'],user_data['ejercicio']))

    rutina = rutinas.getCollection().find_one({'nombre':user_data['rutina']})
    dia = next(x for x in rutina['dia'] if x['nombre'] == user_data['dia'])
    ejercicio = next(x for x in dia['ejercicio'] if x['nombre'] == user_data['ejercicio'])

    #Imágen
    if ejercicio.get('imagen',None):
            data = rutinas.getFs().get(ejercicio['imagen'])
            if data:
                f = open(data.filename, 'wb')
                f.write(data.read())
                f.close()
                bot.sendPhoto(chat_id=update.callback_query.from_user.id, photo=open(utf8(data.filename), 'rb'))
    update.callback_query.edit_message_text('TA!')
    return ConversationHandler.END


def recibir_horas(bot, update, user_data):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    usuario = user_data['usuario']
    logger.info('Actualizar peso ({}) {}'.format(utf8(user_data['usuario']['nombre']),user_data['ejercicio']))

    update.callback_query.edit_message_text("Por favor enviame el peso máximo que podés levantar en {}".format(user_data['ejercicio']))

    return RECIBIR

def guardar_nuevo_peso(bot, update, user_data):
    #bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)

    try:
        nuevo_peso = float(update.message.text)
    except ValueError:
        logger.error("No se puede convertir a float")
        update.message.reply_text("Peso inválido, intenta de nuevo")
        return RECIBIR

    usuario = user_data['usuario']
    logger.info('Guardar nuevo peso ({}) {} {}'.format(utf8(user_data['usuario']['nombre']),user_data['ejercicio'],nuevo_peso))

    usuarios.getCollection().update({'_id':usuario['_id']},
        {'$push':
            {'pesos_maximos':
                {
                    user_data['ejercicio']:nuevo_peso
                }
            }
        }
        )
    user_data['usuario'] = usuarios.getCollection().find_one({'_id':usuario['_id']})
    keyboard = []
    keyboard.append([InlineKeyboardButton('Comenzar',callback_data='comenzar')])
    keyboard.append([InlineKeyboardButton('Cambiar',callback_data='cambiar')])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
    update.message.reply_text('Bien, tu nuevo peso máximo para {} es {}'.format(user_data['ejercicio'],nuevo_peso),reply_markup=reply_markup)
    return HACER_ACTIVIDAD



def acerca_de(bot, update):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    logger.info('Elegir ({}) {}'.format(utf8(usuario['nombre']),update.callback_query.data))

    entrenador = usuarios.getCollection().find_one({'numero':usuario['entrenador']})

    keyboard = [
        [InlineKeyboardButton(text="Entrenar", callback_data='opcion_entrenar'),InlineKeyboardButton(text="Ver", callback_data='opcion_ver')],
        [InlineKeyboardButton(text="Terminar", callback_data='opcion_terminar')]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)

    update.callback_query.answer("Va info...")
    update.callback_query.edit_message_text(text="GymBot es un software para ayudarte a seguir el entrenamiento marcado por tu entrenador, {} cargará rutinas que podrás seguir usando este chat. Es posible también registrar tus sesiones de entrenamiento para discutirlas luego. Por más información sobre los genios que programaron este bot entrá a mgcoders.uy".format(utf8(entrenador['nombre'])), reply_markup=reply_markup)

    return ELEGIR_ACTIVIDAD

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
