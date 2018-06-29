#!/usr/bin/env python3
#
# A library that allows to create an inline calendar keyboard.
# grcanosa https://github.com/grcanosa
#
"""
Base methods for calendar keyboard creation and processing.
"""

import sqlalchemy
from db import Task
import db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
import datetime
import calendar

class TelegramCalendar(object):
    def create_callback_data(self, action, task, year, month, day):
        """ Create the callback data associated to each button"""
        return ";".join([action,str(task),str(year),str(month),str(day)])

    def separate_callback_data(self, data):
        """ Separate the callback data"""
        return data.split(";")


    def create_calendar(self, task, year=None, month=None):
        """
        Create an inline keyboard with the provided year and month
        :param int year: Year to use in the calendar, if None the current year is used.
        :param int month: Month to use in the calendar, if None the current month is used.
        :return: Returns the InlineKeyboardMarkup object with the calendar.
        """
        now = datetime.datetime.now()
        if year == None: year = now.year
        if month == None: month = now.month
        data_ignore = self.create_callback_data("IGNORE", task, year, month, 0)
        keyboard = []
        #First row - Month and Year
        row=[]
        row.append(InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data=data_ignore))
        keyboard.append(row)
        #Second row - Week Days
        row=[]
        for day in ["Mo","Tu","We","Th","Fr","Sa","Su"]:
            row.append(InlineKeyboardButton(day,callback_data=data_ignore))
        keyboard.append(row)

        my_calendar = calendar.monthcalendar(year, month)
        for week in my_calendar:
            row=[]
            for day in week:
                if(day==0):
                    row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
                else:
                    row.append(InlineKeyboardButton(str(day),callback_data=self.create_callback_data("DAY",task,year,month,day)))
            keyboard.append(row)
        #Last row - Buttons
        row=[]
        row.append(InlineKeyboardButton("<",callback_data=self.create_callback_data("PREV-MONTH",task,year,month,day)))
        row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
        row.append(InlineKeyboardButton(">",callback_data=self.create_callback_data("NEXT-MONTH",task,year,month,day)))
        keyboard.append(row)

        return InlineKeyboardMarkup(keyboard)


    def process_calendar_selection(self, bot, update):
        """
        Process the callback_query. This method generates a new calendar if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param telegram.Bot bot: The bot, as provided by the CallbackQueryHandler
        :param telegram.Update update: The update, as provided by the CallbackQueryHandler
        :return: Returns a tuple (Boolean,datetime.datetime), indicating if a date is selected
                    and returning the date if so.
        """
        ret_data = None
        query_callback = update.callback_query
        (action,task,year,month,day) = self.separate_callback_data(query_callback.data)
        curr = datetime.datetime(int(year), int(month), 1)
        selected = False
        task_id = int(task)
        query_db = db.session.query(Task).filter_by(
            id=task_id, chat=query_callback.message.chat_id)
        try:
            task = query_db.one()
        except sqlalchemy.orm.exc.NoResultFound:
            #services.not_found_message(bot, update, task_id)
            return
        if action == "IGNORE":
            bot.answer_callback_query(callback_query_id= query_callback.id)
        elif action == "DAY":
            bot.edit_message_text(text=query_callback.message.text,
                chat_id=query_callback.message.chat_id,
                message_id=query_callback.message.message_id
                )
            ret_data = datetime.datetime(int(year),int(month),int(day))
            task.duedate = ret_data
            db.session.commit()
            selected = True
        elif action == "PREV-MONTH":
            pre = curr - datetime.timedelta(days=1)
            bot.edit_message_text(text=query_callback.message.text,
                chat_id=query_callback.message.chat_id,
                message_id=query_callback.message.message_id,
                reply_markup=self.create_calendar(task_id,int(pre.year),int(pre.month)))
        elif action == "NEXT-MONTH":
            ne = curr + datetime.timedelta(days=31)
            bot.edit_message_text(text=query_callback.message.text,
                chat_id=query_callback.message.chat_id,
                message_id=query_callback.message.message_id,
                reply_markup=self.create_calendar(task_id,int(ne.year),int(ne.month)))
        else:
            bot.answer_callback_query(callback_query_id= query_callback.id,text="Something went wrong!")
            # UNKNOWN
        return selected,ret_data
