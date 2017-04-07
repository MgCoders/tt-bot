#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler,ConversationHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from libs.Repository import Repository

#Sesiones Activas, sustituir por Memcached
sesiones = {}

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
# Estados
IDENTIFICACION, OPCIONES, VER, ELEGIR_ACTIVIDAD, HACER_ACTIVIDAD, REGISTRAR = range(6)
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
        keyboard = [[InlineKeyboardButton(text="Claro!", callback_data='seguir'),InlineKeyboardButton(text="Eh? ¿Esto que es?", callback_data='acerca_de')]]
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
    	logger.info("Usuario conocido %s" % usuario['nombre'])
    	update.message.reply_text("¿Estás list@ %s?" % utf8(usuario['nombre']), reply_markup=reply_markup)
    	return OPCIONES
    keyboard = [[KeyboardButton(text="Enviar número", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text("Hola, parece que no estás registrado, ¿estás de acuerdo en enviarnos tu número para continuar?", reply_markup=reply_markup)
    return IDENTIFICACION
 
def opciones(bot,update):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    logger.info('Opciones ({}), Opción {}'.format(utf8(usuario['nombre']),update.callback_query.data))
    keyboard = [
        [InlineKeyboardButton(text="Entrenar", callback_data='opcion_entrenar'),InlineKeyboardButton(text="Ver sesiones anteriores", callback_data='opcion_ver')],
        [InlineKeyboardButton(text="Terminar", callback_data='opcion_terminar')]
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
        logger.info("Guardamos chat_id del usuario {}".format(update.message.chat_id))
        usuarios.update_one(str(usuario['_id']),'chat_id',update.message.chat_id)
        usuarios.update_one(str(usuario['_id']),'nombre',user.first_name)
        keyboard = [[InlineKeyboardButton(text="Seguir", callback_data='seguir'),InlineKeyboardButton(text="Eh? ¿Esto que es?", callback_data='acerca_de')]]
        reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)
    	logger.info("Usuario conocido %s" % usuario['nombre'])
    	update.message.reply_text("Bienvenido! Soy GymBot el asistente de {}:".format(utf8(entrenador['nombre'])), reply_markup=reply_markup)
    	return OPCIONES
    else:
        update.message.reply_text("Necesitás ser invitado por tu entrenador, nos vemos!",reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
    
def elegir_rutina(bot, update):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    sesiones[update.callback_query.from_user.id] = {'usuario':usuario['nombre']}
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
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    callback_data = eval(update.callback_query.data)
    sesion = sesiones[update.callback_query.from_user.id]
    sesion['rutina'] = callback_data['rutina']
    sesiones[update.callback_query.from_user.id] = sesion
    logger.info('Elegir ({}), Rutina {}'.format(utf8(sesion['usuario']),sesion['rutina']))
    rutina = rutinas.getCollection().find_one({'nombre':sesion['rutina']})
    
    keyboard = []
    for dia in rutina['dia']:
        keyboard.append([InlineKeyboardButton(dia['nombre'],callback_data=str({'dia':dia['nombre']}))])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.callback_query.answer("Excelente! %s" % sesion['rutina'])
    update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
   
    return ELEGIR_ACTIVIDAD  

def elegir_ejercicio(bot, update):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    sesion = sesiones[update.callback_query.from_user.id]
    callback_data = eval(update.callback_query.data)
    sesion['dia'] = callback_data['dia']
    sesiones[update.callback_query.from_user.id] = sesion
    logger.info('Elegir ({}), Rutina {}, Día {}'.format(utf8(sesion['usuario']),sesion['rutina'],sesion['dia']))
    
    rutina = rutinas.getCollection().find_one({'nombre':sesion['rutina']})
    dia = next(x for x in rutina['dia'] if x['nombre'] == sesion['dia'])

    keyboard = []
    for ejercicio in dia['ejercicio']:
        keyboard.append([InlineKeyboardButton(ejercicio['nombre'],callback_data=str({'ejercicio':ejercicio['nombre']}))])
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


    update.callback_query.answer("Vamos con %s!" % callback_data['dia'])
    update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)

    return HACER_ACTIVIDAD 

def hacer_ejercicio(bot, update):
    bot.sendChatAction(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    usuario = usuarios.getCollection().find_one({'chat_id':update.callback_query.from_user.id})
    sesion = sesiones[update.callback_query.from_user.id]
    callback_data = eval(update.callback_query.data)
    sesion['ejercicio'] = callback_data['ejercicio']
    sesiones[update.callback_query.from_user.id] = sesion
    logger.info('Hacer ({}), Rutina {}, Día {}, Ejercicio {}'.format(utf8(sesion['usuario']),sesion['rutina'],sesion['dia'],sesion['ejercicio']))
    
    rutina = rutinas.getCollection().find_one({'nombre':sesion['rutina']})
    dia = next(x for x in rutina['dia'] if x['nombre'] == sesion['dia'])
    ejercicio = next(x for x in dia['ejercicio'] if x['nombre'] == sesion['ejercicio'])

    #Texto
    if (ejercicio['peso_max']):
    	text = "{} consiste en {} series con cargas relativas a tu peso máximo.".format(utf8(sesion['ejercicio']),len(ejercicio['serie']))
    else:
        text = "{} consiste en {} series.".format(utf8(sesion['ejercicio']),len(ejercicio['serie']))

    #Imágen
    if ejercicio.get('imagen',None):
            data = rutinas.getFs().get(ejercicio['imagen'])
            if data:
                f = open(data.filename, 'wb')
                f.write(data.read())
                f.close()
                bot.sendPhoto(chat_id=update.callback_query.from_user.id, photo=open(utf8(data.filename), 'rb'))

    keyboard = [
	[InlineKeyboardButton('Comenzar',callback_data='comenzar')],
	[InlineKeyboardButton('Actualizar Peso Máximo',callback_data='actualizar_peso')],
	[InlineKeyboardButton('Cambiar',callback_data='cambiar')]
	]
    
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=False, one_time_keyboard=True)

    update.callback_query.answer(sesion['ejercicio'])
    update.callback_query.edit_message_text(text=text,reply_markup=reply_markup)

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

    

