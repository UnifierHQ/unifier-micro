"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024  Green, ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging

class CustomFormatter(logging.Formatter):
    """The code in this class was based on code from discord.py.
    Please check EXTERNAL_LICENSES.txt for attribution and licensing info."""
    def __init__(self, count):
        super().__init__()
        log_colors = {
            'debug': '\x1b[45;1m',
            'info': '\x1b[36;1m',
            'warning': '\x1b[33;1m',
            'error': '\x1b[31;1m',
            'critical': '\x1b[37;41m',
        }

        self.log_formats = {
            logging.DEBUG: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U0001F6E0  {log_colors["debug"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            logging.INFO: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U0001F4DC {log_colors["info"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            logging.WARNING: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U00002755 {log_colors["warning"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            logging.ERROR: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U0000274C {log_colors["error"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            logging.CRITICAL: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U0001F6D1 {log_colors["critical"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            'unknown': logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U00002754 %(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            )
        }

    def format(self, log):
        useformat = self.log_formats.get(log.levelno)
        if not useformat:
            useformat = self.log_formats.get('unknown')

        if log.exc_info:
            text = useformat.formatException(log.exc_info)
            log.exc_text = f'\x1b[31m{text}\x1b[0m'
            output = useformat.format(log)
            log.exc_text = None
        else:
            output = useformat.format(log)

        return output

def buildlogger(package, name, level, handler=None):
    if not handler:
        handler = logging.StreamHandler()

    handler.setLevel(level)
    handler.setFormatter(CustomFormatter(len(package) + 15))
    library, _, _ = __name__.partition('.')
    logger = logging.getLogger(package + '.' + name)

    # Prevent duplicate output
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
