#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from telegram.ext import CommandHandler, Updater
from telegram.ext import MessageHandler, Filters
from classes.telegram_handlers import Handler

TOKEN = os.environ.get('MY_API_KEY', None)

def main():
    updater = Updater(token='{}'.format(TOKEN))
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', Handler().start)
    help_handler = CommandHandler('start', Handler().start)
    echo_handler = MessageHandler(Filters.text, Handler().echo)
    new_handler = CommandHandler('new', Handler().new, pass_args=True)
    rename_handler = CommandHandler('rename', Handler().rename, pass_args=True)
    duplicate_handler = CommandHandler('duplicate', Handler().duplicate, pass_args=True)
    delete_handler = CommandHandler('delete', Handler().delete, pass_args=True)
    todo_handler = CommandHandler('todo', Handler().todo, pass_args=True)
    doing_handler = CommandHandler('doing', Handler().doing, pass_args=True)
    done_handler = CommandHandler('done', Handler().done, pass_args=True)
    list_handler = CommandHandler('list', Handler().list)
    dependson_handler = CommandHandler('dependson', Handler().dependson, pass_args=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(new_handler)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(rename_handler)
    dispatcher.add_handler(duplicate_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(todo_handler)
    dispatcher.add_handler(doing_handler)
    dispatcher.add_handler(done_handler)
    dispatcher.add_handler(list_handler)
    dispatcher.add_handler(dependson_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
