#!/usr/bin/env python3

import sys
import pytest

from classes.services import Services
from telegram import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
import datetime
import calendar
from classes.telegramcalendar import TelegramCalendar
import db
from db import Task

class Test(object):
    def test_deps_text(self):
        text = ''
        task1 = Task(chat=1, name='{}'.format(text),
                    status='TODO', dependencies='', parents='', priority='')
        task2 = Task(chat=1, name='{}'.format(text),
                    status='TODO', dependencies='1,2,', parents='', priority='')
        task3 = Task(chat=1, name='{}'.format(text),
                    status='TODO', dependencies='2,', parents='', priority='')
       
        db.session.add(task1)
        db.session.add(task2)
        db.session.add(task3)
        db.session.commit()

        chat = 1
        preceed=''

        assert text == Services().deps_text(task1,chat,preceed)

    def test_separate_callback_data(self):
        text = '22;10;93'
        result = ['22', '10', '93']
        assert result == TelegramCalendar().separate_callback_data(text)

    def test_create_callback_data(self):
        text = ''
        action = 'a'
        year = '18'
        month = '10'
        day = '22'
        task_id = 1
                
        result = 'a;1;18;10;22'
        assert result == TelegramCalendar().create_callback_data(action, task_id, year, month, day)

    def test_create_calendar(self):
        text = ''
        result = ['22', '10', '93']
        year = '12'
        month = '10'
        curr = datetime.datetime(int(year), int(month), 1)
        pre = curr - datetime.timedelta(days=1)
        ne = curr + datetime.timedelta(days=31)

        task_id = 1
        res = TelegramCalendar().create_calendar(task_id,12,10)
        assert res == TelegramCalendar().create_calendar(task_id, int(ne.year), int(ne.month))
