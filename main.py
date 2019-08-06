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
    logger.set_bot(bot.id, bot.bot_async)
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.logger.info("Interrupt signal received,stopping.")


if __name__ == "__main__":
    main()
