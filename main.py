#!/usr/bin/env python3

import os
from classes.handler_updater import HandlerUpdater

TOKEN = os.environ.get('MY_API_KEY', None)

def main():
    handler_updater = HandlerUpdater(TOKEN)
    handler_updater.add_handlers()
    handler_updater.updater_start_polling()

if __name__ == '__main__':
    main()
