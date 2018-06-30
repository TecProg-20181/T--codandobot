#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import sqlalchemy
from telegram import ReplyKeyboardRemove
from db import GithubIssueTable, Task
import db
from classes.telegramcalendar import TelegramCalendar
from classes.github_issue import GithubIssue
from classes.services import Services

TUTORIAL = "https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/"

HELP = """
 /new NAME
 /todo ID
 /doing ID
 /done ID
 /add_date ID
 /delete ID
 /list
 /rename ID NAME
 /depends_on ID ID... or ID {delete} to delete a dependence
 /duplicate ID
 /priority ID PRIORITY{low, medium, high}
 /show_priority
 /my_github_token
 /send_issue ID {github repo} {issue body} {github organization or 0}
                (if your repo isn't in an organization, type "0")
 /help
 /help_github_token
"""

FORMAT = '%(asctime)s -- %(levelname)s -- %(module)s %(lineno)d -- %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
LOGGER = logging.getLogger('root')
LOGGER.info("Running %s", sys.argv[0])
class Handler(object):
    def __init__(self):
        self.services = Services()

    @classmethod
    def __delete_dependency(cls, update, task):
        for i in task.dependencies.split(',')[:-1]:
            i = int(i)
            query_loop = db.session.query(Task).filter_by(
                id=i, chat=update.message.chat_id)
            task_loop = query_loop.one()
            task_loop.parents = task_loop.parents.replace(
                '{},'.format(task.id), '')
        task.dependencies = ''

    def __set_dependency(self, depids, update, task, bot):
        for depid in depids[1:]:
            if depid.isdigit():
                depid = int(depid)
                query = db.session.query(Task).filter_by(id=depid,
                chat=update.message.chat_id)
                try:
                    taskdep = query.one()
                    taskdep.parents += str(task.id) + ','
                except sqlalchemy.orm.exc.NoResultFound:
                    self.services.not_found_message(bot, update, depid)
                    continue

                deplist = task.dependencies.split(',')
                LOGGER.info("Deplist %s", deplist)
                if not self.services.a_is_in_b(update, depid, task):
                    task.dependencies += str(depid) + ','
                    bot.send_message(
                    chat_id=update.message.chat_id,
                    text="Task {} dependencies up to date".format(depid))
                else:
                    bot.send_message(chat_id=update.message.chat_id,
                        text="{} is dependence on some of these numbers.".format(depid))
            else:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="All dependencies ids must be numeric, and not {}"
                    .format(depid))

    @classmethod
    def start(cls, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Welcome! Here is a list of things you can do.")
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(HELP))

    @classmethod
    def new(cls, bot, update, args):
        text = ''
        for each_word in args:
            text += each_word + ' '
        task = Task(chat=update.message.chat_id, name='{}'.format(text),
                    status='TODO', dependencies='', parents='', priority='')
        db.session.add(task)
        db.session.commit()
        bot.send_message(chat_id=update.message.chat_id,
                         text="New task *TODO* [[{}]] {}"
                         .format(task.id, task.name))

    def echo(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="I'm sorry, {}. I'm afraid I can't do {}."
                         .format(self.services.get_name(update), update.message.text))
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(HELP))

    @classmethod
    def help(cls, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Welcome! Here is a list of things you can do.")
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(HELP))

    @classmethod
    def help_github_token(cls, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="To get your token, follow this tutorial:\n{}".format(TUTORIAL))

    def rename(self, bot, update, args):
        text_rename = args[1]
        text = args[0]

        if text.isdigit():
            task_id = int(text)
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.services.not_found_message(bot, update, task_id)
                return

            if text_rename == '':
                bot.send_message(chat_id=update.message.chat_id,
                                 text=("You want to modify task {}," +
                                       " but you didn't provide any new text")
                                 .format(task_id))
                return

            old_text = task.name
            task.name = text_rename
            db.session.commit()
            bot.send_message(chat_id=update.message.chat_id,
                             text="Task {} redefined from {} to {}"
                             .format(task_id, old_text, text_rename))

        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id")

    def duplicate(self, bot, update, args):
        if args[0].isdigit():
            task_id = int(args[0])
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.services.not_found_message(bot, update, task_id)
                return

            dtask = Task(chat=task.chat, name=task.name, status=task.status,
                         dependencies=task.dependencies, parents=task.parents,
                         priority=task.priority, duedate=task.duedate)
            db.session.add(dtask)

            for each_task in task.dependencies.split(',')[:-1]:
                each_query = db.session.query(Task).filter_by(
                    id=int(each_task), chat=update.message.chat_id)
                each_task = each_query.one()
                each_task.parents += '{},'.format(dtask.id)

            db.session.commit()
            bot.send_message(chat_id=update.message.chat_id,
                             text="New task *TODO* [[{}]] {}"
                             .format(dtask.id, dtask.name))
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id")

    def delete(self, bot, update, args):
        for i in args:
            if i.isdigit():
                task_id = int(i)
                task_id = int(args[0])
                query = db.session.query(Task).filter_by(
                    id=task_id, chat=update.message.chat_id)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    self.services.not_found_message(bot, update, task_id)
                    return
                for each_task in task.dependencies.split(',')[:-1]:
                    each_query = db.session.query(Task).filter_by(
                        id=int(each_task), chat=update.message.chat_id)
                    each_task = each_query.one()
                    each_task.parents = each_task.parents.replace('{},'.format(task.id), '')
                db.session.delete(task)
                db.session.commit()
                bot.send_message(chat_id=update.message.chat_id,
                                 text="Task [[{}]] deleted".format(task_id))
            else:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="You must inform the task id")

    def todo(self, bot, update, args):
        for i in args:
            if i.isdigit():
                task_id = int(i)
                query = db.session.query(Task).filter_by(
                    id=task_id, chat=update.message.chat_id)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    self.services.not_found_message(bot, update, task_id)
                    return
                task.status = 'TODO'
                db.session.commit()
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="*TODO* task [[{}]] {}".format(task.id, task.name))
            else:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="You must inform the task id")

    def doing(self, bot, update, args):
        for i in args:
            if i.isdigit():
                task_id = int(i)
                query = db.session.query(Task).filter_by(
                    id=task_id, chat=update.message.chat_id)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    self.services.not_found_message(bot, update, task_id)
                    return
                task.status = 'DOING'
                db.session.commit()
                bot.send_message(
                    chat_id=update.message.chat_id, text="*DOING* task [[{}]] {}"
                    .format(task.id, task.name))
            else:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="You must inform the task id")

    def done(self, bot, update, args):
        for i in args:
            if i.isdigit():
                task_id = int(i)
                query = db.session.query(Task).filter_by(
                    id=task_id, chat=update.message.chat_id)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    self.services.not_found_message(bot, update, task_id)
                    return
                task.status = 'DONE'
                db.session.commit()
                bot.send_message(
                    chat_id=update.message.chat_id, text="*DONE* task [[{}]] {}"
                    .format(task.id, task.name))
            else:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="You must inform the task id")


    def list(self, bot, update):
        message = ''

        message += '📋 Task List\n'
        query = db.session.query(Task).filter_by(
            parents='', chat=update.message.chat_id).order_by(Task.id)
        for task in query.all():
            icon = '🆕'
            if task.status == 'DOING':
                icon = '🔘'
            elif task.status == 'DONE':
                icon = '✔️'

            message += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
            message += self.services.deps_text(task=task, chat=update.message.chat_id)

        bot.send_message(chat_id=update.message.chat_id, text=message)
        message = ''

        message += '📝 _Status_\n'
        query = db.session.query(Task).filter_by(
            status='TODO', chat=update.message.chat_id).order_by(Task.id)
        message += '\n🆕 *TODO*\n'
        for task in query.all():
            if task.duedate != None:
                message += '[[{}]] {} -- Delivery date: {}\n'.format(task.id, task.name, task.duedate)
            else:
                message += '[[{}]] {}\n'.format(task.id, task.name)
        query = db.session.query(Task).filter_by(
            status='DOING', chat=update.message.chat_id).order_by(Task.id)
        message += '\n🔘 *DOING*\n'
        for task in query.all():
            message += '[[{}]] {}\n'.format(task.id, task.name)
        query = db.session.query(Task).filter_by(
            status='DONE', chat=update.message.chat_id).order_by(Task.id)
        message += '\n✔️ *DONE*\n'
        for task in query.all():
            message += '[[{}]] {}\n'.format(task.id, task.name)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def depends_on(self, bot, update, args):
        task_delete = args[1]
        task_id = args[0]
        LOGGER.info("log: %s", args)

        if task_id.isdigit():
            task_id = int(task_id)
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.services.not_found_message(bot, update, task_id)
                return

            if task_delete == 'delete':
                self.__delete_dependency(update, task)
                bot.send_message(chat_id=update.message.chat_id,
                                 text="Dependencies removed from task {}"
                                 .format(task_id))
            else:
                depids = args
                LOGGER.info("depids %s", depids)
                LOGGER.info("depids next %s", depids[1:])

                self.__set_dependency(depids, update, task, bot)

            db.session.commit()
            bot.send_message(
                chat_id=update.message.chat_id,
                text="Task {} dependencies up to date".format(task_id))
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id")

    def priority(self, bot, update, args):
        text_rename = args[1]
        text = args[0]
        if text != '':
            if len(text.split(' ', 1)) > 1:
                text_rename = text.split(' ', 1)[1]
            text = text.split(' ', 1)[0]

        if not text.isdigit():
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id")
        else:
            task_id = int(text)
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.services.not_found_message(bot, update, task_id)
                return

            if text_rename == '':
                task.priority = ''
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="_Cleared_ all priorities from task {}"
                    .format(task_id))
            else:
                if text_rename.lower() not in ['high', 'medium', 'low']:
                    bot.send_message("The priority *must be* one of" +
                                     " the following: high, medium, low")
                else:
                    task.priority = text_rename.lower()
                    bot.send_message(chat_id=update.message.chat_id,
                                     text="*Task {}* priority has priority *{}*"
                                     .format(task_id, text_rename.lower()))
            db.session.commit()

    @classmethod
    def show_priority(cls, bot, update):
        message = ''
        query = db.session.query(Task).filter_by(chat=update.message.chat_id).order_by(Task.id)
        for task in query.all():
            if task.priority == '':
                message += "[[{}]] {} doesn't have priority {}\n".format(task.id, task.name.upper(),
                                                                         task.priority.upper())
            else:
                message += '[[{}]] {} | priority {}\n'.format(task.id, task.name.upper(),
                                                              task.priority.upper())
        bot.send_message(chat_id=update.message.chat_id, text=message)

    @classmethod
    def my_github_token(cls, bot, update, args):
        token = args[0]
        task = GithubIssueTable(id=1, token='{}'.format(token))
        db.session.add(task)
        db.session.commit()
        bot.send_message(chat_id=update.message.chat_id,
                         text="Token {} added!"
                         .format(task.token))

    @classmethod
    def send_issue(cls, bot, update, args):
        task_id = args[0]
        repo_name = args[1]
        issue_body = ''
        organization = args[-1]

        for each_word in args[2:-1]:
            issue_body += each_word + ' '

        if task_id.isdigit():
            task_id = int(task_id)
            try:
                github = db.session.query(GithubIssueTable).filter_by(id='1').one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="Token not found. 🙈")
                return
            try:
                task = db.session.query(Task).filter_by(id=task_id,
                                                        chat=update.message.chat_id).one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="Task not found. 🙈")
                return
            github_issue = GithubIssue(github.token)

            issue_title = task.name
            make_issue = github_issue.make_issue(repo_name, issue_title, issue_body, organization)
            if make_issue != 0:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="Your issue {} was send!"
                                 .format(issue_title))
            else:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="I'm sorry. We couldn't find your repo. 🧐")
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id.")

    def add_date(self, bot, update, args):
        if args[0].isdigit():
            update.message.reply_text("Please select a date: ",
                                      reply_markup=TelegramCalendar().create_calendar(args[0]))
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id.")


    def add_date_function(self, bot, update):
        selected, date = TelegramCalendar().process_calendar_selection(bot, update)
        if selected:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="You selected %s" % (date.strftime("%Y-%m-%d")),
                             reply_markup=ReplyKeyboardRemove())
