#  Pill Posting by jimchen5209
#  Copyright (C) 2018-2019
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

# !/usr/bin/env python

from __future__ import print_function

import sys

from bot import Bot
from config import Config
from logger import Logger


def main():
    # Setup Logging
    logger = Logger()

    # Setup Config
    if len(sys.argv) != 1:
        if sys.argv[1] == 'test':
            config = Config(True)
        else:
            raise SyntaxError("Invalid command syntax: {0}".format(sys.argv[1]))
    else:
        config = Config()

    logger.set_debug(config.Debug)
    bot = Bot(config, logger)
    if len(sys.argv) == 1:
        logger.set_bot(bot.id, bot.bot_async)
    # Setup Config
    if len(sys.argv) != 1:
        if sys.argv[1] == 'test':
            print('There is no syntax error,exiting...')
            exit()
        else:
            raise SyntaxError("Invalid command syntax: {0}".format(sys.argv[1]))
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.logger.info("Interrupt signal received,stopping.")


if __name__ == "__main__":
    main()
