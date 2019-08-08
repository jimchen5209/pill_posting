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

from typing import List, Optional

from bson.objectid import ObjectId
from pymongo import MongoClient
from telepot import Bot

from config import Config
from db_data import Channel, User, Post
from logger import Logger


class PillPosting:
    def __init__(self, bot: Bot, config: Config, logger: Logger):
        self.__config = config
        self.__logger = logger
        self.__logger.logger.info("Connecting to MongoDB Server....")
        self.__mongodb = MongoClient(
            self.__config.MongoDB.ip, self.__config.MongoDB.port)
        self.__db = self.__mongodb[self.__config.MongoDB.name]
        self.__user = self.__db.user
        self.__message_data = self.__db.message_data
        self.__posts = self.__db.posts
        self.__queues = self.__db.queues
        self.__buttons = self.__db.buttons
        self.channels = []
        for i in config.ChannelsRaw:
            self.channels.append(Channel(bot, config, i['channel'], i['owners'], i['groups']))

    # channel admins
    def get_user_affiliated_channel(self, user_id: int) -> List[Channel]:
        channels = []
        for channel in self.channels:
            if user_id in channel.owners:
                channels.append(channel)
        return channels

    # channel groups
    def get_group_affiliated_channel(self, chat_id: int) -> List[Channel]:
        channels = []
        for channel in self.channels:
            if chat_id in channel.groups:
                channels.append(channel)
        return channels

    def get_channel(self, chat_id: int) -> Optional[Channel]:
        for channel in self.channels:
            if chat_id == channel.id:
                return channel
        return None

    # user
    def get_user(self, user_id: int) -> Optional[User]:
        user = self.__user.find_one({'id': user_id})
        return User(user) if user else None

    def set_user_lang(self, user_id: ObjectId, lang: str):
        self.__user.update({'_id': user_id}, {"$set": {'lang': lang}})

    def new_user(self, user_id: int, lang: str):
        self.__user.insert_one({
            'id': user_id,
            'posts': [],
            'lang': lang
        })

    # button
    def new_button(self, callback: dict) -> ObjectId:
        button_id = self.__buttons.insert_one({
            'data': callback
        })
        return button_id.inserted_id

    def get_button(self, button_id: ObjectId) -> Optional[dict]:
        return self.__buttons.find_one({'_id': button_id})

    def remove_button(self, button_id: ObjectId):
        return self.__buttons.delete_one({'_id': button_id})

    # post
    def new_post(self, user_id: int, channels: List[int], post_type: str, messages: List[dict]) -> ObjectId:
        post_id = self.__posts.insert_one({
            'targetChannels': channels,
            'type': post_type,
            'message': messages
        })
        for message in messages:
            self.__message_data.insert_one({
                'chat_id': message['chat']['id'],
                'message_id': message['message_id'],
                'post_id': post_id.inserted_id,
                'type': 'original'
            })
        self.__user.update({'id': user_id}, {'$push': {'posts': post_id.inserted_id}})
        return post_id.inserted_id

    def add_forward(self, post_id: ObjectId, messages: List[dict]):
        for message in messages:
            self.__message_data.insert_one({
                'chat_id': message['chat']['id'],
                'message_id': message['message_id'],
                'post_id': post_id,
                'type': 'forwarded'
            })

    def add_queue(self, post_id: ObjectId, target, message):
        self.__queues.insert_one({
            'post_id': post_id,
            'message': message,
            'target': target
        })

    def get_post_details(self, post_id: ObjectId) -> Optional[Post]:
        post = self.__posts.find_one({'_id': post_id})
        return Post(self, post) if post else None

    def mark_as_sent(self, post_id: ObjectId, target_channel: Channel, posted_message_id: int = -1) -> dict:
        data = {}
        if posted_message_id != -1:
            if target_channel.type == 'public':
                data['url'] = 'https://t.me/{0}/{1}'.format(target_channel.username, str(posted_message_id))
            else:
                data['url'] = 'https://t.me/c/{0}/{1}'.format(target_channel.id[4:], str(posted_message_id))
        data['queues'] = self.__queues.find({'post_id': post_id, 'target': target_channel.id})
        self.__queues.delete_many({'post_id': post_id, 'target': target_channel.id})
        return data

    def mark_as_rejected(self, post_id: ObjectId, target_channel: Channel) -> list:
        data = []
        queues = self.__queues.find({'post_id': post_id, 'target': target_channel.id})
        count = int(queues.count())
        while count > 0:
            data.append(queues.next())
            count -= 1
        self.__queues.delete_many({'post_id': post_id, 'target': target_channel.id})
        return data
