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

from typing import List

from telepot import Bot

from config import Config


class Channel:
    def __init__(self, bot: Bot, config: Config, channel_id: int, owners: List[int], groups: List[int]):
        self.id = channel_id
        self.title = ""
        self.username = ""
        self.type = ""
        self.update_info(bot)
        self.owners = owners
        self.groups = groups
        self.__config = config

    def update_info(self, bot: Bot):
        channel = bot.getChat(self.id)
        self.title = channel['title']
        if 'username' in channel:
            self.type = "public"
            self.username = channel['username']
        else:
            self.type = "private"

    def add_owner(self, user_id: int):
        self.owners.append(user_id)
        self.__config.update_channel(self.id, 'owners', self.owners)

    def remove_owner(self, user_id: int):
        if user_id in self.owners:
            self.owners.remove(user_id)
            self.__config.update_channel(self.id, 'owners', self.owners)
            return True
        else:
            return False

    def add_group(self, chat_id: int):
        self.groups.append(chat_id)
        self.__config.update_channel(self.id, 'groups', self.groups)

    def remove_group(self, chat_id: int):
        if chat_id in self.groups:
            self.groups.remove(chat_id)
            self.__config.update_channel(self.id, 'groups', self.groups)
            return True
        else:
            return False


class User:
    def __init__(self, user: dict):
        self.id = user['_id']
        self.bot_id = user['id']
        self.posts = user['posts']
        self.lang = user['lang']


class Post:
    def __init__(self, pill_posting, post: dict):
        channels = []
        for channel_id in post['targetChannels']:
            channel = pill_posting.get_channel(channel_id)
            if channel:
                channels.append(channel)
        self.target_channels = channels
        self.post_type = post['type']
        self.messages = post['messages']