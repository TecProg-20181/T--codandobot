#!/usr/bin/env python3
import sys
import logging
import db
from db import Task

FORMAT = '%(asctime)s -- %(levelname)s -- %(module)s %(lineno)d -- %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
LOGGER = logging.getLogger('root')
LOGGER.info("Running %s", sys.argv[0])

class Services(object):
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
    def a_is_in_b(self, update, dependency_id, task):
        if task.parents != '':

            task_id = task.parents.split(',')
            task_id.pop()

            dependency_list = [int(id) for id in task_id]

            if dependency_id in dependency_list:
                return True
            else:
                query = db.session.query(Task).filter_by(id=dependency_list[0],
                                                chat=update.message.chat_id).one()
                
                task_id = query.one()
                return self.a_is_in_b(update, task_id, task)

        return False

    @classmethod
    def not_found_message(cls, bot, update, task_id):
        bot.send_message(
            chat_id=update.message.chat_id,
            text="_404_ Task {} not found 🙈".format(task_id))
