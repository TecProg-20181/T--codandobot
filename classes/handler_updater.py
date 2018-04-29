#!/usr/bin/env python3

from telegram.ext import CommandHandler, Updater
from telegram.ext import MessageHandler, Filters
from classes.telegram_handlers import Handler


class HandlerUpdater(object):
    def __init__(self, token):
        self.token = token
        self.updater = Updater(token='{}'.format(self.token))
        self.dispatcher = self.updater.dispatcher

    @classmethod
    def __command_handlers_github(cls, task_command):
        handler = Handler()
        command_handler = None
        if task_command == 'my_github_token_handler':
            command_handler = CommandHandler('my_github_token_handler', handler.my_github_token, pass_args=True)
        elif task_command == 'send_issue_handler':
            command_handler = CommandHandler('send_issue', handler.send_issue, pass_args=True)
        return command_handler

    @classmethod
    def __command_handlers_show(cls, task_command):
        handler = Handler()
        command_handler = None
        if task_command == 'start_handler':
            command_handler = CommandHandler('start', handler.start)
        elif task_command == 'help_handler':
            command_handler = CommandHandler('help', handler.help)
        elif task_command == 'echo_handler':
            command_handler = MessageHandler(Filters.text, handler.echo)
        elif task_command == 'show_priority_handler':
            command_handler = CommandHandler('show_priority', handler.show_priority)
        elif task_command == 'list_handler':
            command_handler = CommandHandler('list', handler.list)
        return command_handler

    @classmethod
    def __command_handlers_pass_args(cls, task_command):
        handler = Handler()
        command_handler = None
        if task_command == 'new_handler':
            command_handler = CommandHandler('new', handler.new, pass_args=True)
        elif task_command == 'rename_handler':
            command_handler = CommandHandler('rename', handler.rename, pass_args=True)
        elif task_command == 'duplicate_handler':
            command_handler = CommandHandler('duplicate', handler.duplicate,
                                             pass_args=True)
        elif task_command == 'delete_handler':
            command_handler = CommandHandler('delete', handler.delete, pass_args=True)
        elif task_command == 'todo_handler':
            command_handler = CommandHandler('todo', handler.todo, pass_args=True)
        elif task_command == 'doing_handler':
            command_handler = CommandHandler('doing', handler.doing, pass_args=True)
        elif task_command == 'done_handler':
            command_handler = CommandHandler('done', handler.done, pass_args=True)
        elif task_command == 'priority_handler':
            command_handler = CommandHandler('priority', handler.priority,
                                             pass_args=True)
        elif task_command == 'dependson_handler':
            command_handler = CommandHandler('dependson', handler.dependson,
                                             pass_args=True)
        return command_handler

    def add_handlers(self):
        self.dispatcher.add_handler(self.__command_handlers_pass_args('new_handler'))
        self.dispatcher.add_handler(self.__command_handlers_pass_args('rename_handler'))
        self.dispatcher.add_handler(self.__command_handlers_pass_args('duplicate_handler'))
        self.dispatcher.add_handler(self.__command_handlers_pass_args('delete_handler'))
        self.dispatcher.add_handler(self.__command_handlers_pass_args('todo_handler'))
        self.dispatcher.add_handler(self.__command_handlers_pass_args('doing_handler'))
        self.dispatcher.add_handler(self.__command_handlers_pass_args('done_handler'))
        self.dispatcher.add_handler(self.__command_handlers_pass_args('dependson_handler'))
        self.dispatcher.add_handler(self.__command_handlers_pass_args('priority_handler'))
        self.dispatcher.add_handler(self.__command_handlers_github('my_github_token_handler'))
        self.dispatcher.add_handler(self.__command_handlers_github('send_issue_handler'))
        self.dispatcher.add_handler(self.__command_handlers_show('show_priority_handler'))
        self.dispatcher.add_handler(self.__command_handlers_show('start_handler'))
        self.dispatcher.add_handler(self.__command_handlers_show('help_handler'))
        self.dispatcher.add_handler(self.__command_handlers_show('list_handler'))
        self.dispatcher.add_handler(self.__command_handlers_show('echo_handler'))

    def updater_start_polling(self):
        self.updater.start_polling()
