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
from typing import List

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
            await self.auto_register(message)
            return
        if message.content_type == 'text' and message.message_text.startswith("/"):
            await self.__handle_command(message)
            return
        await self.__handle_hash_tag(message)
        pass

    async def handle_supergroup(self, message: Message):
        group = self.pill_posting.get_group_affiliated_channel(message.chat.id)
        if len(group) == 0 and message.chat.id not in self.__config.Admin_groups:
            debug_raw_message = await self.bot_async.sendMessage(
                message.chat.id,
                "I am not for this group",
                reply_to_message_id=message.id
            )
            self.__logger.logger.debug("Raw sent message: {0}".format(str(debug_raw_message)))
            await self.bot_async.leaveChat(message.chat.id)
            return
        if message.content_type == 'text' and message.message_text.startswith("/"):
            if not message.from_user.db_user:
                await self.auto_register(message)
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

    async def auto_register(self, message: Message):
        start_up_message = await self.bot_async.sendMessage(
            message.chat.id,
            "Trying to fetch language from your account...",
            reply_to_message_id=message.id
        )
        self.__logger.logger.debug("Raw sent message: {0}".format(str(start_up_message)))
        lang = message.from_user.language_code
        if not self.__lang.test_lang(lang):
            lang = 'en'
        lang_list = self.__lang.lang_list(callback_type='register')
        buttons = []
        for lang_data in lang_list:
            name = lang_data['name']
            callback = self.queue_button(lang_data['pre_callback'])
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
            self.__lang.lang('register.choose_lang', lang).format(
                language=self.__lang.lang('lang.name', lang, fallback=False)),
            reply_markup=markup
        )

    def queue_button(self, data: dict) -> dict:
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
    async def command_change_language(self, args: List[str], message: Message):
        user = message.from_user.db_user
        start_up_message = await self.bot_async.sendMessage(
            message.chat.id,
            self.__lang.lang('lang.try', user.lang),
            reply_to_message_id=message.id
        )
        self.__logger.logger.debug("Raw sent message: {0}".format(str(start_up_message)))
        lang = message.from_user.language_code
        if not self.__lang.test_lang(lang):
            lang = ''
        lang_list = self.__lang.lang_list()
        buttons = []
        for lang_data in lang_list:
            name = lang_data['name']
            callback = self.queue_button(lang_data['pre_callback'])
            if lang_data['key'] == lang:
                name += " ☑️"
            if lang_data['key'] == user.lang:
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
                old_language=self.__lang.lang('lang.name', user.lang, fallback=False)),
            reply_markup=markup
        )

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
    async def __handle_hash_tag(self, message: Message):
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
                await self.auto_register(message)
                return
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
                await method(message)

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
        lang = callback.data.actions['value']
        self.pill_posting.new_user(callback.from_user.id, lang)
        message_identifier = telepot.message_identifier(callback.button_message.raw_message)
        await self.bot_async.editMessageText(
            message_identifier,
            self.__lang.lang('register.success', lang).format(
                language=self.__lang.lang('lang.name', lang, fallback=False)))
        self.__locked_button.remove(callback.data.button_id)
        self.__cleanup_button(callback.button_message)

    async def callback_set_lang(self, callback: Callback):
        user = callback.from_user.db_user
        lang = callback.data.actions['value']
        self.pill_posting.set_lang(user.id, lang)
        message_identifier = telepot.message_identifier(callback.button_message.raw_message)
        await self.bot_async.editMessageText(
            message_identifier,
            self.__lang.lang('lang.set.success', lang).format(
                language=self.__lang.lang('lang.name', lang, fallback=False)))
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
