#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import urllib
import os
import sys
import requests
import sqlalchemy
import telegram
import logging
from telegram.ext import CommandHandler, Updater
from telegram.ext import MessageHandler, Filters
from db import Task
import db

TOKEN = os.environ.get('MY_API_KEY', None)
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
BOT = telegram.Bot(token='{}'.format(TOKEN))

HELP = """
 /new NOME
 /todo ID
 /doing ID
 /done ID
 /delete ID
 /list
 /rename ID NOME
 /dependson ID ID...
 /duplicate ID
 /priority ID PRIORITY{low, medium, high}
 /help
"""

FORMAT = '%(asctime)s -- %(levelname)s -- %(module)s %(lineno)d -- %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger('root')
logger.info("Running " + sys.argv[0])


def get_name(update):
    try:
        name = update.message.from_user.first_name
    except (NameError, AttributeError):
        try:
            name = update.message.from_user.username
        except (NameError, AttributeError):
            logger.info("No username or first name..")
            return ""
    return name


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Welcome! Here is a list of things you can do.")
    bot.send_message(chat_id=update.message.chat_id, text="{}".format(HELP))

def new(bot, update, args):
    task = Task(chat=update.message.chat_id, name='{}'.format(args[0]), status='TODO',
                dependencies='', parents='', priority='')
    db.session.add(task)
    db.session.commit()
    bot.send_message(
        chat_id=update.message.chat_id, text="New task *TODO* [[{}]] {}".format(task.id, task.name))

def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm sorry {}. I'm afraid I can't do that.".format(str(update.message.from_user.username)))
    bot.send_message(chat_id=update.message.chat_id, text="{}".format(HELP))
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)

def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Welcome! Here is a list of things you can do.")
    bot.send_message(chat_id=update.message.chat_id, text="{}".format(HELP))

def caps(bot, update, text):
    text_caps = ' '.join(text).upper()
    bot.send_message(chat_id=update.message.chat_id, text=text_caps)


def rename(bot, update, args):
    text_rename = args[1]
    text = args[0]
    if text != '':
        if len(text.split(' ', 1)) > 1:
            text_rename = text.split(' ', 1)[1]
        text = text.split(' ', 1)[0]

    if text.isdigit():
        task_id = int(text)
        query = db.session.query(Task).filter_by(id=task_id, chat=update.message.chat_id)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            bot.send_message(
                chat_id=update.message.chat_id, text="_404_ Task {} not found x.x".format(task_id))
            return

        if text_rename == '':
            bot.send_message(
                chat_id=update.message.chat_id, text="You want to modify task {}, but you didn't provide any new text".format(task_id))
            return

        old_text = task.name
        task.name = text_rename
        db.session.commit()
        bot.send_message(chat_id=update.message.chat_id, text="Task {} redefined from {} to {}".format(
            task_id, old_text, text_rename))

    else:
        bot.send_message(chat_id=update.message.chat_id, text="You must inform the task id")

def duplicate(bot, update, args):
    if args[0].isdigit():
        task_id = int(args[0])
        query = db.session.query(Task).filter_by(id=task_id, chat=update.message.chat_id)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            bot.send_message(
                chat_id=update.message.chat_id, text="_404_ Task {} not found x.x".format(task_id))
            return

        dtask = Task(chat=task.chat, name=task.name, status=task.status, dependencies=task.dependencies,
                     parents=task.parents, priority=task.priority, duedate=task.duedate)
        db.session.add(dtask)

        for t in task.dependencies.split(',')[:-1]:
            qy = db.session.query(Task).filter_by(id=int(t), chat=update.message.chat_id)
            t = qy.one()
            t.parents += '{},'.format(dtask.id)

        db.session.commit()
        bot.send_message(
            chat_id=update.message.chat_id, text="New task *TODO* [[{}]] {}".format(dtask.id, dtask.name))
    else:
        bot.send_message(chat_id=update.message.chat_id, text="You must inform the task id")

def delete(bot, update, args):
    if args[0].isdigit():
        task_id = int(args[0])
        query = db.session.query(Task).filter_by(id=task_id, chat=update.message.chat_id)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            bot.send_message(
                chat_id=update.message.chat_id, text="_404_ Task {} not found x.x".format(task_id))
            return
        for t in task.dependencies.split(',')[:-1]:
            qy = db.session.query(Task).filter_by(id=int(t), chat=update.message.chat_id)
            t = qy.one()
            t.parents = t.parents.replace('{},'.format(task.id), '')
        db.session.delete(task)
        db.session.commit()
        bot.send_message(chat_id=update.message.chat_id, text="Task [[{}]] deleted".format(task_id))
    else:
        bot.send_message(chat_id=update.message.chat_id, text="You must inform the task id")

def todo(bot, update, args):
    if args[0].isdigit():
        task_id = int(args[0])
        query = db.session.query(Task).filter_by(id=task_id, chat=update.message.chat_id)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            bot.send_message(
                chat_id=update.message.chat_id, text="_404_ Task {} not found x.x".format(task_id))
            return
        task.status = 'TODO'
        db.session.commit()
        bot.send_message(
            chat_id=update.message.chat_id, text="*TODO* task [[{}]] {}".format(task.id, task.name))
    else:
        bot.send_message(chat_id=update.message.chat_id, text="You must inform the task id")

def doing(bot, update, args):
    if args[0].isdigit():
        task_id = int(args[0])
        query = db.session.query(Task).filter_by(id=task_id, chat=update.message.chat_id)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            bot.send_message(
                chat_id=update.message.chat_id, text="_404_ Task {} not found x.x".format(task_id))
            return
        task.status = 'DOING'
        db.session.commit()
        bot.send_message(
            chat_id=update.message.chat_id, text="*DOING* task [[{}]] {}".format(task.id, task.name))
    else:
        bot.send_message(chat_id=update.message.chat_id, text="You must inform the task id")

def done(bot, update, args):
    if args[0].isdigit():
        task_id = int(args[0])
        query = db.session.query(Task).filter_by(id=task_id, chat=update.message.chat_id)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            bot.send_message(
                chat_id=update.message.chat_id, text="_404_ Task {} not found x.x".format(task_id))
            return
        task.status = 'DONE'
        db.session.commit()
        bot.send_message(
            chat_id=update.message.chat_id, text="*DONE* task [[{}]] {}".format(task.id, task.name))
    else:
        bot.send_message(chat_id=update.message.chat_id, text="You must inform the task id")

def list(bot, update):
    a = ''

    a += '\U0001F4CB Task List\n'
    query = db.session.query(Task).filter_by(
        parents='', chat=update.message.chat_id).order_by(Task.id)
    for task in query.all():
        icon = '\U0001F195'
        if task.status == 'DOING':
            icon = '\U000023FA'
        elif task.status == 'DONE':
            icon = '\U00002611'

        a += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
        a += deps_text(task, update.message.chat_id)

    bot.send_message(chat_id=update.message.chat_id, text=a)
    a = ''

    a += '\U0001F4DD _Status_\n'
    query = db.session.query(Task).filter_by(
        status='TODO', chat=update.message.chat_id).order_by(Task.id)
    a += '\n\U0001F195 *TODO*\n'
    for task in query.all():
        a += '[[{}]] {}\n'.format(task.id, task.name)
    query = db.session.query(Task).filter_by(
        status='DOING', chat=update.message.chat_id).order_by(Task.id)
    a += '\n\U000023FA *DOING*\n'
    for task in query.all():
        a += '[[{}]] {}\n'.format(task.id, task.name)
    query = db.session.query(Task).filter_by(
        status='DONE', chat=update.message.chat_id).order_by(Task.id)
    a += '\n\U00002611 *DONE*\n'
    for task in query.all():
        a += '[[{}]] {}\n'.format(task.id, task.name)

    bot.send_message(chat_id=update.message.chat_id, text=a)

def dependson(bot, update, args):
    text_rename = args[1]
    text = args[0]
    if text != '':
        if len(text.split(' ', 1)) > 1:
            text_rename = text.split(' ', 1)[1]
        text = text.split(' ', 1)[0]

    if not text.isdigit():
        bot.send_message(chat_id=update.message.chat_id, text="You must inform the task id")
    else:
        task_id = int(text)
        query = db.session.query(Task).filter_by(id=task_id, chat=update.message.chat_id)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            bot.send_message(
                chat_id=update.message.chat_id, text="_404_ Task {} not found x.x".format(task_id))
            return

        if text_rename == '':
            for i in task.dependencies.split(',')[:-1]:
                i = int(i)
                q = db.session.query(Task).filter_by(id=i, chat=update.message.chat_id)
                t = q.one()
                t.parents = t.parents.replace(
                    '{},'.format(task.id), '')

            task.dependencies = ''
            bot.send_message(
                chat_id=update.message.chat_id, text="Dependencies removed from task {}".format(task_id))
        else:
            for depid in text.split(' '):
                if not depid.isdigit():
                    bot.send_message(
                        chat_id=update.message.chat_id, text="All dependencies ids must be numeric, and not {}".format(depid))
                else:
                    depid = int(depid)
                    query = db.session.query(
                        Task).filter_by(id=depid, chat=update.message.chat_id)
                    try:
                        taskdep = query.one()
                        taskdep.parents += str(task.id) + ','
                    except sqlalchemy.orm.exc.NoResultFound:
                        bot.send_message(
                            chat_id=update.message.chat_id, text="_404_ Task {} not found x.x".format(depid))
                        continue

                    deplist = task.dependencies.split(',')
                    if str(depid) not in deplist:
                        task.dependencies += str(depid) + ','

        db.session.commit()
        bot.send_message(
            chat_id=update.message.chat_id, text="Task {} dependencies up to date".format(task_id))

def priority(bot, update, args):
    text_rename = args[1]
    text = args[0]
    if text != '':
        if len(text.split(' ', 1)) > 1:
            text_rename = text.split(' ', 1)[1]
        text = text.split(' ', 1)[0]

    if not text.isdigit():
        bot.send_message(chat_id=update.message.chat_id, text="You must inform the task id")
    else:
        task_id = int(text_rename)
        query = db.session.query(Task).filter_by(id=task_id, chat=update.message.chat_id)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            bot.send_message(
                chat_id=update.message.chat_id, text="_404_ Task {} not found x.x".format(task_id))
            return

        if text_rename == '':
            task.priority = ''
            bot.send_message(
                chat_id=update.message.chat_id, text="_Cleared_ all priorities from task {}".format(task_id))
        else:
            if text.lower() not in ['high', 'medium', 'low']:
                bot.send_message(
                    "The priority *must be* one of the following: high, medium, low")
            else:
                task.priority = text.lower()
                bot.send_message(
                    chat_id=update.message.chat_id, text="*Task {}* priority has priority *{}*".format(task_id, text.lower()))
        db.session.commit()


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))

    return max(update_ids)


def deps_text(task, chat, preceed=''):
    text = ''

    for i in range(len(task.dependencies.split(',')[:-1])):
        line = preceed
        query = db.session.query(Task).filter_by(
            id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
        dep = query.one()

        icon = '\U0001F195'
        if dep.status == 'DOING':
            icon = '\U000023FA'
        elif dep.status == 'DONE':
            icon = '\U00002611'

        if i + 1 == len(task.dependencies.split(',')[:-1]):
            line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '    ')
        else:
            line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '│   ')

        text += line

    return text

def main():
    # last_update_id = None
    #
    # while True:
    #     print("Updates")
    #     updates = get_updates(last_update_id)
    #
    #     if len(updates["result"]) > 0:
    #         last_update_id = get_last_update_id(updates) + 1
    #         handle_updates(BOT,updates)
    #
    #     time.sleep(0.5)

    updater = Updater(token='{}'.format(TOKEN))
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(Filters.text, echo)
    new_handler = CommandHandler('new', new, pass_args=True)
    rename_handler = CommandHandler('rename', rename, pass_args=True)
    duplicate_handler = CommandHandler('duplicate', duplicate, pass_args=True)
    delete_handler = CommandHandler('delete', delete, pass_args=True)
    todo_handler = CommandHandler('todo', todo, pass_args=True)
    doing_handler = CommandHandler('doing', doing, pass_args=True)
    done_handler = CommandHandler('done', done, pass_args=True)
    list_handler = CommandHandler('list', list)
    dependson_handler = CommandHandler('dependson', dependson, pass_args=True)
    dispatcher.add_handler(start_handler)
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
