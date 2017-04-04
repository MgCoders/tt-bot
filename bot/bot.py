#!/bin/python
# -*- coding: utf-8 -*-


import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from libs.bot_utils import start,echo,caps,inline_caps,button,contact

keys = {}
exec(open('libs/key_all.py').read(), keys)

updater = Updater(token=keys['telegram'])
dispatcher = updater.dispatcher


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(CallbackQueryHandler(button))

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

contact_handler = MessageHandler(Filters.contact, contact)
dispatcher.add_handler(contact_handler)


updater.start_polling()
updater.idle()





