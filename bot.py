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

import asyncio
import json
import sys
from typing import List, Optional

import telepot.aio
from bson.objectid import ObjectId
from telepot.aio.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from bot_data import Message, Callback
from config import Config
from lang import Lang
from logger import Logger
from pill_posting import PillPosting


class Bot:
    __alias_hash_tag = {
        "投稿": "post",
        "markassent": "mark_as_sent",
        "markascancelled": "mark_as_cancelled"
    }

    __locked_button = []
    __message_queue = {}

    def __init__(self, config: Config, logger: Logger):
        self.__config = config
        self.__logger = logger
        self.__lang = Lang()
        if len(sys.argv) == 1:
            self.bot = telepot.Bot(config.TOKEN)
            self.bot_async = telepot.aio.Bot(config.TOKEN)

            me = self.bot.getMe()
            self.id = me['id']
            self.username = me['username']
            self.nick = me['first_name']
            self.pill_posting = PillPosting(self.bot, config, logger)

    # main
    async def on_chat_message(self, msg: dict):
        await self.__logger.log_msg(msg)
        message = Message(self.pill_posting, msg)
        name = "handle_{0}".format(message.chat.type)
        try:
            method = getattr(self, name)
        except AttributeError:
            self.__logger.logger.error(
                "Could not handle {chat_type}, is it a new type?".format(chat_type=message.chat.type))
        else:
            await method(message)

    async def handle_private(self, message: Message):
        if not message.from_user.db_user:
            await self.__register_user(message)
            return
        if message.content_type == 'text' and message.message_text.startswith("/"):
            await self.__handle_command(message)
            return
        if await self.__handle_hash_tag(message) == 0:
            await self.__queue_post_message(message)
        pass

    async def handle_supergroup(self, message: Message):
        # leave unknown group
        if len(message.chat.affiliated_channel) == 0 and message.chat.id not in self.__config.Admin_groups:
            debug_raw_message = await self.bot_async.sendMessage(
                message.chat.id,
                "I am not for this group",
                reply_to_message_id=message.id
            )
            self.__logger.logger.debug("Raw sent message: {0}".format(str(debug_raw_message)))
            await self.bot_async.leaveChat(message.chat.id)
            return
        # auto register group
        if not message.chat.db_group:
            await self.__set_group_lang(message)
            return
        # command
        if message.content_type == 'text' and message.message_text.startswith("/"):
            # auto register user
            if not message.from_user.db_user:
                await self.__register_user(message)
                return
            await self.__handle_command(message)
            return
        await self.__handle_hash_tag(message)

    async def handle_group(self, message: Message):
        await self.handle_supergroup(message)

    async def handle_channel(self, message: Message):
        channel = self.pill_posting.get_channel(message.chat.id)
        if channel is not None and message.content_type == 'new_chat_title':
            old_title = channel.title
            channel.update_info(self.bot)
            for group in list(dict.fromkeys(self.__config.Admin_groups + channel.groups)):
                await self.bot_async.sendMessage(
                    group,
                    "{old_title} 已更改頻道名稱為 {new_title}".format(old_title=old_title, new_title=message.chat.name)
                )

    async def __queue_post_message(self, message: Message):
        if message.from_user.id not in self.__message_queue:
            self.__message_queue[message.from_user.id] = {
                "queue": [],
                "last_message": {},
                "button": None
            }
            self.__message_queue[message.from_user.id]['queue'].append(message.raw_message)
            callback_data_post = {
                'type': 'start_posting',
                'actions': {}
            }
            callback_data_refresh = {
                'type': 'refresh',
                'actions': {'value': 'post_queue'}
            }
            callback_data_cancel = {
                'type': 'cancel',
                'actions': {'value': 'post_queue'}
            }
            button = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=self.__lang.lang('post.finish', message.from_user.db_user.lang),
                    callback_data=json.dumps(self.__queue_button(callback_data_post), ensure_ascii=False)
                )
            ],
                [
                    InlineKeyboardButton(
                        text=self.__lang.lang('post.refresh', message.from_user.db_user.lang),
                        callback_data=json.dumps(self.__queue_button(callback_data_refresh), ensure_ascii=False)
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=self.__lang.lang('post.cancel', message.from_user.db_user.lang),
                        callback_data=json.dumps(self.__queue_button(callback_data_cancel), ensure_ascii=False)
                    )
                ]
            ])
            self.__message_queue[message.from_user.id]['button'] = button

            sent_message = await self.bot_async.sendMessage(
                message.chat.id,
                self.__lang.lang('post.queue', message.from_user.db_user.lang).format(
                    count=str(len(self.__message_queue[message.from_user.id]['queue']))
                ),
                reply_to_message_id=message.id,
                reply_markup=self.__message_queue[message.from_user.id]['button']
            )
            self.__logger.logger.debug("Raw sent message: {0}".format(str(sent_message)))

            self.__message_queue[message.from_user.id]['last_message'] = sent_message
        else:
            self.__message_queue[message.from_user.id]['queue'].append(message.raw_message)
            if self.__message_queue[message.from_user.id]['last_message'] != {}:
                try:
                    message_identifier = telepot.message_identifier(
                        self.__message_queue[message.from_user.id]['last_message'])
                    await self.bot_async.editMessageText(
                        message_identifier,
                        self.__lang.lang('post.queue', message.from_user.db_user.lang).format(
                            count=str(len(self.__message_queue[message.from_user.id]['queue']))
                        ),
                        reply_markup=self.__message_queue[message.from_user.id]['button']
                    )
                except telepot.exception.TelegramError as e:
                    self.__logger.logger.error("Error when deleting previous message: {0}".format(str(e.args)))

    async def __set_group_lang(self, message: Message, re_handle: bool = True):
        lang_list = self.__lang.lang_list(
            callback_type='set_group_lang',
            re_handle=message.raw_message if re_handle else None
        )
        buttons = []
        for lang_data in lang_list:
            name = lang_data['name']
            callback = self.__queue_button(lang_data['pre_callback'])
            buttons.append([InlineKeyboardButton(
                text=name,
                callback_data=json.dumps(callback, ensure_ascii=False)
            )])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await self.bot_async.sendMessage(
            message.chat.id,
            self.__lang.lang('lang.group.choose_lang'),
            reply_to_message_id=message.id,
            reply_markup=markup
        )

    async def __register_user(self, message: Message):
        await self.__set_user_language(message, callback_type='register', re_handle=message.raw_message)

    async def __set_user_language(
            self,
            message: Message,
            callback_type: str = 'set_lang',
            re_handle: Optional[dict] = None
    ):
        user = message.from_user.db_user

        start_up_message = await self.bot_async.sendMessage(
            message.chat.id,
            "Trying to fetch language from your account..." if not user else self.__lang.lang('lang.try', user.lang),
            reply_to_message_id=message.id
        )
        self.__logger.logger.debug("Raw sent message: {0}".format(str(start_up_message)))

        lang = message.from_user.language_code
        if not self.__lang.test_lang(lang):
            lang = 'en'

        lang_list = self.__lang.lang_list(callback_type=callback_type, re_handle=re_handle)

        buttons = []
        for lang_data in lang_list:
            name = lang_data['name']
            callback = self.__queue_button(lang_data['pre_callback'])
            if user:
                if lang_data['key'] == lang:
                    name += " ☑️"
                if lang_data['key'] == user.lang:
                    name += " ✅"
            else:
                if lang_data['key'] == lang:
                    name += " ✅"

            buttons.append([InlineKeyboardButton(
                text=name,
                callback_data=json.dumps(callback, ensure_ascii=False)
            )])

        message_identify = telepot.message_identifier(start_up_message)
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await self.bot_async.editMessageText(
            message_identify,
            self.__lang.lang('lang.choose_lang', user.lang).format(
                language=self.__lang.lang('lang.name', lang, fallback=False),
                old_language=self.__lang.lang('lang.name', user.lang, fallback=False)
            ) if callback_type == 'set_lang' else
            self.__lang.lang('register.choose_lang', lang).format(
                language=self.__lang.lang('lang.name', lang, fallback=False)
            ),
            reply_markup=markup
        )

    def __queue_button(self, data: dict) -> dict:
        button_id = self.pill_posting.new_button(data)
        return {'button_id': str(button_id)}

    # command
    async def __handle_command(self, message: Message):
        user = message.from_user.db_user
        raw = message.message_text.split(" ")
        command = raw[0].lower()[1:]
        args = raw[1:]
        if command.find("@") != -1:
            if command.find("@" + self.username) == -1:
                return
            command = command.replace("@" + self.username, "")
        name = "command_{0}".format(command)
        try:
            method = getattr(self, name)
        except AttributeError:
            await self.bot_async.sendMessage(
                message.chat.id,
                self.__lang.lang('command.not_found', user.lang).format(command=command),
                reply_to_message_id=message.id
            )
        else:
            await method(args, message)

    # noinspection PyUnusedLocal
    async def command_start(self, args: List[str], message: Message):
        user = message.from_user.db_user
        await self.bot_async.sendMessage(
            message.chat.id,
            self.__lang.lang('bot.message.start', lang=user.lang).format(user=message.from_user.name),
            reply_to_message_id=message.id
        )

    async def command_new_post(self, args: List[str], message: Message):
        await self.bot_async.sendMessage(
            message.chat.id,
            "已觸發 /new_post (新投稿)",
            reply_to_message_id=message.id
        )
        pass

    async def command_action(self, args: List[str], message: Message):
        await self.bot_async.sendMessage(
            message.chat.id,
            "已觸發 /action (再次操作訊息)",
            reply_to_message_id=message.id
        )
        pass

    async def command_add_owner(self, args: List[str], message: Message):
        await self.bot_async.sendMessage(
            message.chat.id,
            "已觸發 /add_owner (增加頻道管理員)",
            reply_to_message_id=message.id
        )
        pass

    async def command_remove_owner(self, args: List[str], message: Message):
        await self.bot_async.sendMessage(
            message.chat.id,
            "已觸發 /remove_owner (移除頻道管理員)",
            reply_to_message_id=message.id
        )
        pass

    async def command_add_group(self, args: List[str], message: Message):
        await self.bot_async.sendMessage(
            message.chat.id,
            "已觸發 /add_group (增加頻道群組)",
            reply_to_message_id=message.id
        )
        pass

    async def command_remove_group(self, args: List[str], message: Message):
        await self.bot_async.sendMessage(
            message.chat.id,
            "已觸發 /remove_group (移除頻道群組)",
            reply_to_message_id=message.id
        )
        pass

    # noinspection PyUnusedLocal
    async def command_change_group_language(self, args: List[str], message: Message):
        if message.chat.type == 'group' or message.chat.type == 'supergroup':
            await self.__set_group_lang(message, re_handle=False)
        else:
            user = message.from_user.db_user
            await self.bot_async.sendMessage(
                message.chat.id,
                self.__lang.lang("command.group_only", user.lang if user else 'en'),
                reply_to_message_id=message.id
            )

    # noinspection PyUnusedLocal
    async def command_change_language(self, args: List[str], message: Message):
        await self.__set_user_language(message)

    # noinspection PyUnusedLocal
    async def command_help(self, args: List[str], message: Message):
        user = message.from_user.db_user
        text = self.__lang.lang('command.list', user.lang)
        methods = [func for func in dir(self) if callable(getattr(self, func)) and func.startswith("command_")]
        for command in methods:
            text += "\n {0}".format(command.replace("command_", "/"))
        raw_sent_message = await self.bot_async.sendMessage(message.chat.id, text, reply_to_message_id=message.id)
        self.__logger.logger.debug("Raw sent message: {0}".format(str(raw_sent_message)))

    # hash tag
    async def __handle_hash_tag(self, message: Message) -> int:
        triggered_count = 0
        user = message.from_user.db_user
        raw = message.message_text.split(" ")
        tag_names = []
        for text in raw:
            if text.startswith("#"):
                tag_name = text[1:].lower()
                for i in self.__alias_hash_tag:
                    tag_name = tag_name.replace(i, self.__alias_hash_tag[i])
                tag_names.append(tag_name)
        tag_names = list(dict.fromkeys(tag_names))
        if len(tag_names) != 0:
            if not user:
                await self.__register_user(message)
                return -1
        if 'mark_as_sent' in tag_names and 'mark_as_cancelled' in tag_names:
            tag_names.remove("mark_as_sent")
            tag_names.remove("mark_as_cancelled")
            await self.bot_async.sendMessage(
                message.chat.id,
                self.__lang.lang("hash_tag.contradiction", user.lang).format("#mark_as_send", "#mark_as_cancelled"),
                reply_to_message_id=message.id)
        for tag_name in tag_names:
            name = "hash_tag_{0}".format(tag_name)
            try:
                method = getattr(self, name)
            except AttributeError:
                pass
            else:
                triggered_count += 1
                await method(message)
        return triggered_count

    async def hash_tag_post(self, message: Message):
        await self.bot_async.sendMessage(
            message.chat.id,
            "已觸發 #投稿 (以回覆訊息新增投稿)",
            reply_to_message_id=message.id
        )
        pass

    async def hash_tag_mark_as_sent(self, message: Message):
        await self.bot_async.sendMessage(
            message.chat.id,
            "已觸發 #mark_as_sent (強制標記該投稿為已傳送)",
            reply_to_message_id=message.id
        )
        pass

    async def hash_tag_mark_as_cancelled(self, message: Message):
        await self.bot_async.sendMessage(
            message.chat.id,
            "已觸發 #mark_as_cancelled (強制標記該投稿為已撤銷)",
            reply_to_message_id=message.id
        )
        pass

    async def on_callback_query(self, msg: dict):
        self.__logger.logger.debug("Raw query data: {0}".format(msg))
        try:
            callback = Callback(self.pill_posting, msg)
        except Exception as e:
            self.__logger.logger.error(
                "Error parsing callback data: {0}, perhaps it's from other bot?".format(str(type(e)) + str(e.args)))
            await self.bot_async.answerCallbackQuery(
                msg['id'],
                "Could not parse this button correctly, perhaps it's from other bot?\n\n{0}".format(str(e.args)))
            return
        user = callback.from_user.db_user
        if callback.from_user.id != callback.bot_reply_message.from_user.id:
            await self.bot_async.answerCallbackQuery(
                msg['id'],
                ("Do not touch the button for {user}" if not user else
                 self.__lang.lang("callback.button_not_yours", user.lang)).format(
                    user=callback.bot_reply_message.from_user.name
                )
            )
            return
        if callback.data.button_id in self.__locked_button:
            await self.bot_async.answerCallbackQuery(
                callback.query_id,
                "Button in use" if not user else self.__lang.lang('callback.button_in_use', user.lang))
            return

        if not callback.data.is_valid:
            await self.bot_async.answerCallbackQuery(
                callback.query_id,
                "Button invalid or expired" if not user else self.__lang.lang('callback.button_expired', user.lang))
            return

        name = "callback_{0}".format(callback.data.callback_type)
        try:
            method = getattr(self, name)
        except AttributeError:
            text = "Unknown callback type: {callback_type}".format(callback_type=callback.data.callback_type)
            self.__logger.logger.error(text)
            await self.bot_async.answerCallbackQuery(callback.query_id, text)
        else:
            self.__locked_button.append(callback.data.button_id)
            await method(callback)

    async def callback_register(self, callback: Callback):
        user = callback.from_user.db_user

        lang = callback.data.actions['value']
        if not user:
            self.pill_posting.new_user(callback.from_user.id, lang)
        message_identifier = telepot.message_identifier(callback.button_message.raw_message)
        if user:
            await self.bot_async.editMessageText(
                message_identifier,
                self.__lang.lang('register.exist', user.lang).format(command='/change_language'))
        else:
            await self.bot_async.editMessageText(
                message_identifier,
                self.__lang.lang('register.success', lang).format(
                    language=self.__lang.lang('lang.name', lang, fallback=False)))
        self.__locked_button.remove(callback.data.button_id)
        self.__cleanup_button(callback.button_message)
        if 'handle' in callback.data.actions and len(callback.data.actions['handle']) != 0:
            self.__logger.logger.info("Re_handling message")
            await self.on_chat_message(callback.data.actions['handle'])

    async def callback_set_lang(self, callback: Callback):
        if 'value' not in callback.data.actions:
            return
        user = callback.from_user.db_user
        lang = callback.data.actions['value']
        self.pill_posting.set_user_lang(user.id, lang)
        message_identifier = telepot.message_identifier(callback.button_message.raw_message)
        await self.bot_async.editMessageText(
            message_identifier,
            self.__lang.lang('lang.set.success', lang).format(
                language=self.__lang.lang('lang.name', lang, fallback=False)))
        self.__locked_button.remove(callback.data.button_id)
        self.__cleanup_button(callback.button_message)

    async def callback_set_group_lang(self, callback: Callback):
        if 'value' not in callback.data.actions:
            return
        group = callback.bot_reply_message.chat.db_group
        lang = callback.data.actions['value']
        if group:
            self.pill_posting.set_group_language(callback.bot_reply_message.chat.id, lang)
        else:
            self.pill_posting.add_group(callback.bot_reply_message.chat.id, lang)
        message_identifier = telepot.message_identifier(callback.button_message.raw_message)
        await self.bot_async.editMessageText(
            message_identifier,
            self.__lang.lang('lang.group.set.success', lang).format(
                language=self.__lang.lang('lang.name', lang, fallback=False)))
        self.__locked_button.remove(callback.data.button_id)
        self.__cleanup_button(callback.button_message)
        if 'handle' in callback.data.actions and len(callback.data.actions['handle']) != 0:
            self.__logger.logger.info("Re_handling message")
            await self.on_chat_message(callback.data.actions['handle'])

    async def callback_start_posting(self, callback: Callback):
        pass

    async def callback_refresh(self, callback: Callback):
        if 'value' not in callback.data.actions:
            return
        if callback.data.actions['value'] == 'post_queue':
            lang = callback.from_user.db_user.lang
            message_identifier = telepot.message_identifier(
                self.__message_queue[callback.from_user.id]['last_message'])
            await self.bot_async.editMessageText(
                message_identifier,
                self.__lang.lang('post.queue', lang).format(
                    count=str(len(self.__message_queue[callback.from_user.id]['queue']))
                ),
                reply_markup=self.__message_queue[callback.from_user.id]['button']
            )
            self.__locked_button.remove(callback.data.button_id)

    async def callback_cancel(self, callback: Callback):
        if 'value' not in callback.data.actions:
            return
        if callback.data.actions['value'] == 'post_queue':
            lang = callback.from_user.db_user.lang
            message_identifier = telepot.message_identifier(callback.button_message.raw_message)
            await self.bot_async.editMessageText(
                message_identifier,
                self.__lang.lang('callback.action.cancelled', lang)
            )
            self.__locked_button.remove(callback.data.button_id)
            self.__cleanup_button(callback.button_message)

    def __cleanup_button(self, message: Message):
        if not message.reply_markup:
            return
        if 'inline_keyboard' not in message.reply_markup:
            return
        buttons = message.reply_markup['inline_keyboard']
        for row in buttons:
            for button in row:
                if 'button_id' in button['callback_data']:
                    self.pill_posting.remove_button(ObjectId(json.loads(button['callback_data'])['button_id']))

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(
            MessageLoop(self.bot_async, {
                'chat': self.on_chat_message,
                'callback_query': self.on_callback_query
            }
                        ).run_forever()
        )
        self.__logger.logger.info("Bot has started")
        self.__logger.logger.info("Listening ...")
        loop.run_forever()
