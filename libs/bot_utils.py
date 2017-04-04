#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)


def start(bot, update):
    keyboard = [[KeyboardButton(text="Enviar número", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    logger.info("Bot Started")
    update.message.reply_text("¿Estás de acuerdo en enviarnos tu número para continuar?", reply_markup=reply_markup)
    
def button(bot, update):
    user = update.message.from_user
    logger.info("Contact received from %s" % user.first_name)
    query = update.callback_query
    logger.info("Phone number %s" % query)
    reply_markup = ReplyKeyboardHide()
    bot.editMessageText(text="Selected option: %s" % query.data,
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,reply_markup=reply_markup)
                        
def contact(bot, update):
    user = update.message.from_user
    logger.info("Contact received from %s" % user.first_name)

    logger.info("Phone number %s" % update.message.contact.phone_number)
    reply_markup = ReplyKeyboardRemove()
    update.message.reply_text("Gracias!", reply_markup=reply_markup)
    
def echo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=update.message.text)
    
def caps(bot, update, args):
    text_caps = ' '.join(args).upper()
    bot.sendMessage(chat_id=update.message.chat_id, text=text_caps)
    
def inline_caps(bot, update):
    query = update.inline_query.query
    if not query:
        return
    results = list()
    results.append(
    InlineQueryResultArticle(
        id=query.upper(),
        title='Caps',
        input_message_content=InputTextMessageContent(query.upper())
        )
    )
    bot.answerInlineQuery(update.inline_query.id, results)
