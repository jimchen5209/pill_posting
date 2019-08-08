#!/usr/bin/env python

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

from __future__ import print_function

import json
import logging
import os
from typing import List, Optional


class Lang:
    __lang = {}

    def __init__(self):
        self.__logger = logging.getLogger("Translation")
        logging.basicConfig(level=logging.INFO)
        self.__lang_load_list = []
        self.__lang_list = []
        if not os.path.isdir("lang/"):
            os.mkdir("lang/")
        self.__find_lang("lang/")
        self.__logger.info("Loading languages: {0}".format(", ".join(self.__lang_load_list)))
        for lang_file in self.__lang_load_list:
            try:
                with open(lang_file, "r", encoding='utf8') as fs:
                    self.__lang[os.path.splitext(os.path.basename(lang_file))[0]] = json.load(fs)
            except FileNotFoundError:
                self.__logger.warning("{lang} not found, some string may not work.".format(lang=lang_file))
            except json.decoder.JSONDecodeError as e:
                self.__logger.error(
                    "Error when loading {lang} and skipped, some string may not work.".format(lang=lang_file))
                self.__logger.error(str(e))
                continue

    def __find_lang(self, folder: str):
        for walk in os.walk(folder):
            for file in walk[2]:
                if file.find(".json") != -1:
                    self.__lang_load_list.append(walk[0].replace('\\', '/') + "/" + file)
                    self.__lang_list.append(os.path.splitext(file)[0])

    def test_lang(self, lang: str) -> bool:
        return lang in self.__lang_list

    def lang_list(self, callback_type: str = 'set_lang', re_handle: Optional[dict] = None) -> List[dict]:
        lang_list = []
        for lang in self.__lang_list:
            lang_list.append({
                'name': self.lang('lang.name', lang=lang, fallback=False),
                'key': lang,
                'pre_callback': {'type': callback_type, 'actions': {'value': lang,
                                                                    'handle': {} if not re_handle else re_handle}}
            })
        return lang_list

    def lang(self, lang_id: str, lang: str = 'en', fallback: bool = True) -> str:
        if lang_id in self.__lang[lang]:
            return self.__lang[lang][lang_id]
        elif lang_id in self.__lang['en'] and fallback:
            return self.__lang['en'][lang_id]
        else:
            return lang_id
