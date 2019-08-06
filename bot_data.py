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

import json

from bson.objectid import ObjectId
from telepot import all_content_types

from pill_posting import PillPosting


class Callback:
    def __init__(self, pill_posting: PillPosting, msg: dict):
        self.button_message = Message(pill_posting, msg['message'])
        self.bot_reply_message = Message(pill_posting, msg['message']['reply_to_message'])
        self.query_id = msg['id']
        self.from_user = User(pill_posting, msg['from'])
        self.data = CallbackData(pill_posting, json.loads(msg['data']))


class CallbackData:
    def __init__(self, pill_posting: PillPosting, callback_data: dict):
        self.button_id = callback_data['button_id']
        button_data = pill_posting.get_button(ObjectId(self.button_id))
        self.is_valid = button_data is not None
        self.callback_type = button_data['data']['type'] if button_data else None
        self.actions = button_data['data']['actions'] if button_data else None


class Message:
    def __init__(self, pill_posting: PillPosting, msg: dict):
        def get_first_key(x: dict) -> str:
            for k in all_content_types:
                if k in x:
                    return k

        self.raw_message = msg
        self.content_type = get_first_key(msg)
        self.id = msg['message_id']
        self.edited = 'edit_date' in msg
        self.chat = Chat(msg['chat'])
        self.reply_to_message = Message(pill_posting, msg['reply_to_message']) if 'reply_to_message' in msg else None
        self.from_user = User(pill_posting, msg['from']) if self.chat.type != 'channel' else None
        self.message_text = msg['text'] if self.content_type == 'text' else msg['caption'] if 'caption' in msg else ''
        self.media = None if self.content_type == 'text' else msg[self.content_type]
        self.reply_markup = msg['reply_markup'] if 'reply_markup' in msg else None


class User:
    def __init__(self, pill_posting: PillPosting, user: dict):
        self.id = user['id']
        self.name = user['first_name']
        if 'last_name' in user:
            self.name += " " + user['last_name']
        self.username = user['username'] if 'username' in user else None
        self.language_code = user['language_code'] if 'language_code' in user else 'en'
        self.bot = user['is_bot']
        self.db_user = pill_posting.get_user(self.id)


class Chat:
    def __init__(self, chat: dict):
        self.id = chat['id']
        self.type = chat['type']
        self.name = chat['title'] if self.type != 'private' else chat['first_name']
        if self.type == 'private':
            if 'last_name' in chat:
                self.name += " " + chat['last_name']
        self.username = chat['username'] if 'username' in chat else None
        self.public = ('username' in chat) if self.type != 'private' else None
        self.all_members_are_administrators = chat['all_members_are_administrators'] if self.type == 'group' else False
