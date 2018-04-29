#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import sqlalchemy
from db import Task
from db import GithubIssueTable
import db
from classes.github_issue import GithubIssue

HELP = """
 /new NAME
 /todo ID
 /doing ID
 /done ID
 /delete ID
 /list
 /rename ID NAME
 /dependson ID ID...
 /duplicate ID
 /priority ID PRIORITY{low, medium, high}
 /show_priority
 /my_github_token
 /send_issue TODOID {github repo} {github organization} {issue body}
 /help
"""

FORMAT = '%(asctime)s -- %(levelname)s -- %(module)s %(lineno)d -- %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
LOGGER = logging.getLogger('root')
LOGGER.info("Running %s", sys.argv[0])

class Handler(object):

    def deps_text(self, task, chat, preceed=''):
        text = ''

        for i in range(len(task.dependencies.split(',')[:-1])):
            line = preceed
            query = db.session.query(Task).filter_by(
                id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
            dep = query.one()

            icon = '🆕'
            if dep.status == 'DOING':
                icon = '🔘'
            elif dep.status == 'DONE':
                icon = '✔️'

            if i + 1 == len(task.dependencies.split(',')[:-1]):
                line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '    ')
            else:
                line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '│   ')

            text += line

        return text

    @classmethod
    def get_name(cls, update):
        try:
            name = update.message.from_user.first_name
        except (NameError, AttributeError):
            try:
                name = update.message.from_user.username
            except (NameError, AttributeError):
                LOGGER.info("No username or first name..")
                return ""
        return name

    @classmethod
    def start(cls, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Welcome! Here is a list of things you can do.")
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(HELP))

    @classmethod
    def new(cls, bot, update, args):
        task = Task(chat=update.message.chat_id, name='{}'.format(args[0]),
                    status='TODO', dependencies='', parents='', priority='')
        db.session.add(task)
        db.session.commit()
        bot.send_message(chat_id=update.message.chat_id,
                         text="New task *TODO* [[{}]] {}"
                         .format(task.id, task.name))

    @classmethod
    def echo(cls, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="I'm sorry, {}. I'm afraid I can't do {}."
                         .format(cls.get_name(update), update.message.text))
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(HELP))

    @classmethod
    def help(cls, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Welcome! Here is a list of things you can do.")
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(HELP))

    @classmethod
    def rename(cls, bot, update, args):
        text_rename = args[1]
        text = args[0]

        if text.isdigit():
            task_id = int(text)
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="_404_ Task {} not found 🙈"
                                 .format(task_id))
                return

            if text_rename == '':
                bot.send_message(chat_id=update.message.chat_id,
                                 text="You want to modify task {}, but you didn't provide any new text"
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

    @classmethod
    def duplicate(cls, bot, update, args):
        if args[0].isdigit():
            task_id = int(args[0])
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="_404_ Task {} not found 🙈".format(task_id))
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

    @classmethod
    def delete(cls, bot, update, args):
        if args[0].isdigit():
            task_id = int(args[0])
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="_404_ Task {} not found 🙈".format(task_id))
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

    @classmethod
    def todo(cls, bot, update, args):
        if args[0].isdigit():
            task_id = int(args[0])
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="_404_ Task {} not found 🙈".format(task_id))
                return
            task.status = 'TODO'
            db.session.commit()
            bot.send_message(
                chat_id=update.message.chat_id,
                text="*TODO* task [[{}]] {}".format(task.id, task.name))
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id")

    @classmethod
    def doing(cls, bot, update, args):
        if args[0].isdigit():
            task_id = int(args[0])
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="_404_ Task {} not found 🙈".format(task_id))
                return
            task.status = 'DOING'
            db.session.commit()
            bot.send_message(
                chat_id=update.message.chat_id, text="*DOING* task [[{}]] {}"
                .format(task.id, task.name))
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id")

    @classmethod
    def done(cls, bot, update, args):
        if args[0].isdigit():
            task_id = int(args[0])
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="_404_ Task {} not found 🙈".format(task_id))
                return
            task.status = 'DONE'
            db.session.commit()
            bot.send_message(
                chat_id=update.message.chat_id, text="*DONE* task [[{}]] {}"
                .format(task.id, task.name))
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id")

    @classmethod
    def list(cls, bot, update):
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
            # message += cls.deps_text(cls,task=task, chat=update.message.chat_id)

        bot.send_message(chat_id=update.message.chat_id, text=message)
        message = ''

        message += '📝 _Status_\n'
        query = db.session.query(Task).filter_by(
            status='TODO', chat=update.message.chat_id).order_by(Task.id)
        message += '\n🆕 *TODO*\n'
        for task in query.all():
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

    @classmethod
    def dependson(cls, bot, update, args):
        text_rename = args[1]
        task_id = args[0]
        if task_id.isdigit():
            task_id = int(task_id)
            query = db.session.query(Task).filter_by(
                id=task_id, chat=update.message.chat_id)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="_404_ Task {} not found 🙈"
                                 .format(task_id))
                return

            if text_rename == '':
                for i in task.dependencies.split(',')[:-1]:
                    i = int(i)
                    query_loop = db.session.query(Task).filter_by(
                        id=i, chat=update.message.chat_id)
                    task_loop = query_loop.one()
                    task_loop.parents = task_loop.parents.replace(
                        '{},'.format(task.id), '')

                task.dependencies = ''
                bot.send_message(chat_id=update.message.chat_id,
                                 text="Dependencies removed from task {}"
                                 .format(task_id))
            else:
                depids = args
                LOGGER.info("depids %s", depids)
                LOGGER.info("depids next %s", depids[1:])

                for depid in depids[1:]:
                    if depid.isdigit():
                        depid = int(depid)
                        query = db.session.query(Task).filter_by(id=depid,
                                                                 chat=update.message.chat_id)
                        try:
                            taskdep = query.one()
                            taskdep.parents += str(task.id) + ','
                        except sqlalchemy.orm.exc.NoResultFound:
                            bot.send_message(
                                chat_id=update.message.chat_id,
                                text="_404_ Task {} not found 🙈"
                                .format(depid))
                            continue

                        deplist = task.dependencies.split(',')
                        LOGGER.info("Deplist %s", deplist)
                        if str(depid) not in deplist:
                            task.dependencies += str(depid) + ','
                    else:
                        bot.send_message(
                            chat_id=update.message.chat_id,
                            text="All dependencies ids must be numeric, and not {}"
                            .format(depid))

            db.session.commit()
            bot.send_message(
                chat_id=update.message.chat_id,
                text="Task {} dependencies up to date".format(task_id))
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id")

    @classmethod
    def priority(cls, bot, update, args):
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
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="_404_ Task {} not found 🙈".format(task_id))
                return

            if text_rename == '':
                task.priority = ''
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="_Cleared_ all priorities from task {}"
                    .format(task_id))
            else:
                if text_rename.lower() not in ['high', 'medium', 'low']:
                    bot.send_message("The priority *must be* one of the following: high, medium, low")
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
        issue_body = args[3]
        organization = args[2]

        if task_id.isdigit():
            task_id = int(task_id)
            github_query = db.session.query(GithubIssueTable).filter_by(id='1')
            query_task = db.session.query(Task).filter_by(id=task_id,
                                                          chat=update.message.chat_id)
            try:
                github = github_query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="Token not found 🙈")
                return
            try:
                task = query_task.one()
            except sqlalchemy.orm.exc.NoResultFound:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="Task not found 🙈")
                return
            github_issue = GithubIssue(github.token)

            issue_title = task.name
            github_issue.make_issue(repo_name, issue_title, issue_body, organization)
            bot.send_message(chat_id=update.message.chat_id,
                             text="Your issue {} was send!"
                             .format(issue_title))
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="You must inform the task id")
