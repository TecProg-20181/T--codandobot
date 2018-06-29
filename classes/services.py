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

    # @classmethod
    # def a_is_in_b(cls, update, a, b):
    #     out = True
    #     for i in b:
    #         i = str(i)
    #         query = db.session.query(Task).filter_by(
    #             id=i, chat=update.message.chat_id).one()
    #         LOGGER.info("QUERY_BLA %s", query)
    #         if any('{}'.format(a) in string for string in query.dependencies):
    #             LOGGER.info("Is contained in.")
    #             out = True
    #             break
    #         else:
    #             LOGGER.info("Is not contained in.")
    #             out = False
    #             continue
    #     return out

    @classmethod
    def not_found_message(cls, bot, update, task_id):
        bot.send_message(
            chat_id=update.message.chat_id,
            text="_404_ Task {} not found 🙈".format(task_id))

    def a_is_in_b(self, update, dependency_id, task_id):

        is_circular = False
        task = db.session.query(Task).filter_by(id=dependency_id,
                                                chat=update.message.chat_id).one()
        dependencies = task.dependencies.split(',')

        for i in dependencies:
            if i == '':
                continue
            query = db.session.query(Task).filter_by(
                id=i, chat=update.message.chat_id).one()

            another_dependency = task.dependencies.split(',')
            if task.id in another_dependency:
                is_circular = True
            else:
                partial = self.a_is_in_b(update, query.id, task_id)
                is_circular = is_circular | partial

        return is_circular
