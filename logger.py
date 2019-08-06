#!/usr/bin/env python

from __future__ import print_function

import logging
import os
import time
from datetime import datetime

import telepot
from telepot.aio import Bot


class Logger:
    __logPath = "./logs/{0}".format(time.strftime("%Y-%m-%d-%H-%M-%S"))
    __bot_id = -1
    __bot = None

    def __init__(self):
        if not os.path.isdir("./logs"):
            os.mkdir("./logs")
        self.__log_format = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
        logging.root.name = "PillPosting"
        self.logger = logging.getLogger()
        logging.basicConfig(format=self.__log_format, level=logging.INFO)

        self.__handler = logging.FileHandler(
            filename="{0}.log".format(self.__logPath),
            encoding="utf-8",
            mode="w"
        )
        self.__handler.level = logging.INFO
        self.__handler.setFormatter(logging.Formatter(self.__log_format))
        self.logger.addHandler(self.__handler)

    def set_bot(self, bot_id: int, bot: Bot):
        self.__bot_id = bot_id
        self.__bot = bot

    def set_debug(self, debug=False):
        if debug:
            debug_handler = logging.FileHandler(
                filename="{0}-debug.log".format(self.__logPath),
                encoding="utf-8",
                mode="w"
            )
            self.logger.setLevel(logging.DEBUG)
            debug_handler.level = logging.DEBUG
            debug_handler.setFormatter(logging.Formatter(self.__log_format))
            self.logger.addHandler(debug_handler)
            debug_handler.addFilter(self)
            self.logger.debug("Debug mode has been turned on!")

    @staticmethod
    def filter(log_record):
        return log_record.levelno == logging.DEBUG

    async def log_msg(self, msg: dict):
        content_type, chat_type, chat_id = telepot.glance(msg)
        self.logger.debug("Raw message: {0}".format(msg))
        dlog = "[{0}]".format(time.strftime("%Y-%m-%d-%H-%M-%S"))
        flog = ""
        if 'edit_date' in msg:
            dlog += "[EDITED {0}]".format(
                datetime.utcfromtimestamp(msg['edit_date']).strftime('%Y-%m-%d-%H-%M-%S'))
        if 'from' in msg:
            fromNick = msg['from']['first_name']
            if 'last_name' in msg['from']:
                fromNick += ' {0}'.format(msg['from']['last_name'])
            if 'username' in msg['from']:
                fromNick += ' @{0}'.format(msg['from']['username'])
            fromNick += ' ({0})'.format(str(msg['from']['id']))
        else:
            fromNick = "Channel Admin"

        if chat_type == 'private':
            dlog += "[Private]"
        dlog += "[ID {0}]".format(str(msg['message_id']))

        if 'reply_to_message' in msg:
            reply_to_message = "ID: {0}".format(str(msg['reply_to_message']['message_id']))
            if 'text' in msg['reply_to_message']:
                reply_to_message += " Text: {0}".format(
                    (msg['reply_to_message']['text'][:5] + "...") if len(msg['reply_to_message']['text']) > 5
                    else msg['reply_to_message']['text'])
            if 'caption' in msg['reply_to_message']:
                reply_to_message += " Caption: {0}".format(
                    (msg['reply_to_message']['caption'][:5] + "...") if len(msg['reply_to_message']['caption']) > 5
                    else msg['reply_to_message']['caption'])
            if chat_type != 'channel':
                reply_to_user = msg['reply_to_message']['from']
                if reply_to_user['id'] == self.__bot_id:
                    dlog += " (Reply to my message {0})".format(reply_to_message)
                else:
                    reply_to_nick = reply_to_user['first_name']
                    if 'last_name' in reply_to_user:
                        reply_to_nick += " {0}".format(reply_to_user['last_name'])
                    if 'username' in reply_to_user:
                        reply_to_nick += " @{0}".format(reply_to_user['username'])
                    reply_to_nick += " ({0})".format(str(reply_to_user['id']))
                    dlog += " (Reply to {0}'s message {1})".format(reply_to_nick, reply_to_message)

        if chat_type == 'private':
            if content_type == 'text':
                dlog += ' {0} : {1}'.format(fromNick, msg['text'])
            else:
                dlog += ' {0} sent a {1}'.format(fromNick, content_type)
        elif chat_type == 'group' or chat_type == 'supergroup' or chat_type == 'channel':
            chatTitle = "{0} (ID: {1})".format(msg['chat']['title'], str(chat_id))
            if content_type == 'text':
                dlog += ' {0} in {1} : {2}'.format(fromNick, chatTitle, msg['text'])
            elif content_type == 'new_chat_member':
                newChatMembers = msg['new_chat_members']
                if len(newChatMembers) == 1:
                    newChatMember = msg['new_chat_member']
                    if newChatMember['id'] == self.__bot_id:
                        dlog += ' I have been added to {0} by {1}'.format(
                            chatTitle, fromNick)
                    elif newChatMember['id'] == msg['from']['id']:
                        dlog += " {0} joined {1}".format(fromNick, chatTitle)
                    else:
                        newMemberNick = newChatMember['first_name']
                        if 'last_name' in newChatMember:
                            newMemberNick += " {0}".format(newChatMember['last_name'])
                        if 'username' in newChatMember:
                            newMemberNick += " @{0}".format(newChatMember['username'])
                        newMemberNick += " ({0})".format(newChatMember['id'])
                        dlog += " {0} was added to {1} by {2}".format(newMemberNick, chatTitle, fromNick)
                else:
                    newMembersNick = []
                    for newChatMember in newChatMembers:
                        if newChatMember['id'] == self.__bot_id:
                            newMembersNick.append("me")
                        else:
                            newMemberNick = newChatMember['first_name']
                            if 'last_name' in newChatMember:
                                newMemberNick += " {0}".format(newChatMember['last_name'])
                            if 'username' in newChatMember:
                                newMemberNick += " @{0}".format(newChatMember['username'])
                            newMemberNick += " ({0})".format(newChatMember['id'])
                            newMembersNick.append(newMemberNick)
                    if 'me' in newMembersNick:
                        newMembersNick.remove('me')
                        newMembersNick.append('me')
                    dlog += " {0} were added to {1} by {2}".format(",".join(newMembersNick), chatTitle, fromNick)
            elif content_type == 'left_chat_member':
                leftChatMember = msg['left_chat_member']
                if leftChatMember['id'] == self.__bot_id:
                    dlog += ' I have been kicked from {0} by {1}'.format(chatTitle, fromNick)
                elif leftChatMember['id'] == msg['from']['id']:
                    dlog += ' {0} left {1}'.format(fromNick, chatTitle)
                else:
                    leftMemberNick = leftChatMember['first_name']
                    if 'last_name' in leftChatMember:
                        leftMemberNick += " {0}".format(leftChatMember['last_name'])
                    if 'username' in leftChatMember:
                        leftMemberNick += " @{0}".format(leftChatMember['username'])
                    leftMemberNick += "({0})".format(leftChatMember['id'])
                    dlog += " {0} was kicked from {1} by {2}".format(leftMemberNick, chatTitle, fromNick)
            elif content_type == 'pinned_message':
                pinnedMessage = msg['pinned_message']
                pinnedMessageText = "ID: {0}".format(str(pinnedMessage['message_id']))
                if 'text' in pinnedMessage:
                    pinnedMessageText += " Text: {0}".format(
                        (pinnedMessage['text'][:5] + "...") if len(pinnedMessage['text']) > 5
                        else pinnedMessage['text'])
                if 'caption' in pinnedMessage:
                    pinnedMessageText += " Caption: {0}".format(
                        (pinnedMessage['caption'][:5] + "...") if len(pinnedMessage['caption']) > 5
                        else pinnedMessage['caption'])
                if chat_type != 'channel':
                    pinnedMessageAuthor = pinnedMessage['from']
                    authorNick = pinnedMessageAuthor['first_name']
                    if 'last_name' in pinnedMessageAuthor:
                        authorNick += " {0}".format(pinnedMessageAuthor['last_name'])
                    if 'username' in pinnedMessageAuthor:
                        authorNick += " @{0}".format(pinnedMessageAuthor['username'])
                    authorNick += " ({0})".format(str(pinnedMessageAuthor['id']))
                    dlog += " {0}'s message({1}) was pinned to {2} by {3}".format(authorNick, pinnedMessageText,
                                                                                  chatTitle, fromNick)
                else:
                    dlog += " A message({0}) was pinned to {1} by {2}".format(pinnedMessageText, chatTitle, fromNick)
                pinnedContentType = telepot.glance(pinnedMessage)
                if pinnedContentType != 'text':
                    self.__log_media(pinnedContentType, pinnedMessage)
            elif content_type == 'new_chat_photo':
                dlog += " The photo of {0} was changed by {1}".format(chatTitle, fromNick)
                flog = "[New Chat Photo]"
                photo_array = msg['new_chat_photo']
                photo_array.reverse()
                if 'caption' in msg:
                    flog = flog + "Caption : {0} FileID: {1}".format(msg['caption'], photo_array[0]['file_id'])
                else:
                    flog = flog + "FileID: {0}".format(photo_array[0]['file_id'])
            elif content_type == 'group_chat_created':
                if msg['new_chat_member']['id'] == self.__bot_id:
                    dlog += ' {0} created {1} and I was added into the group.'.format(fromNick, chatTitle)
            elif content_type == 'migrate_to_chat_id':
                newGroup = await self.__bot.getChat(msg['migrate_to_chat_id'])
                newGroupTitle = "{0} (ID: {1})".format(newGroup['title'], str(newGroup['id']))
                dlog += ' The group {0} has upgraded to {1}'.format(chatTitle, newGroupTitle)
            elif content_type == 'migrate_from_chat_id':
                oldGroup = await self.__bot.getChat(msg['migrate_from_chat_id'])
                oldGroupTitle = "{0} (ID: {1})".format(oldGroup['title'], str(oldGroup['id']))
                dlog += ' I was successfully merged from {0} to {1}.'.format(oldGroupTitle, chatTitle)
            elif content_type == 'delete_chat_photo':
                dlog += " The photo of {0} was removed by {1}".format(chatTitle, fromNick)
            elif content_type == 'new_chat_title':
                dlog += " The title of {0} was updated to {1}".format(chatTitle, msg['new_chat_title'])
            else:
                dlog += ' {0} in {1} sent a {2}'.format(fromNick, chatTitle, content_type)
        self.logger.info(dlog)
        self.__log_media(content_type, msg)
        if flog != "":
            self.logger.info(flog)
        return

    def __log_media(self, content_type: str, msg: dict):
        flog = ""
        fileID = ""
        if content_type == 'photo':
            flog = "[Photo]"
            photo_array = msg['photo']
            photo_array.reverse()
            fileID = photo_array[0]['file_id']
        elif content_type == 'audio':
            flog = "[Audio]"
            fileID = msg['audio']['file_id']
        elif content_type == 'document':
            flog = "[Document]"
            fileID = msg['document']['file_id']
        elif content_type == 'video':
            flog = "[Video]"
            fileID = msg['video']['file_id']
        elif content_type == 'voice':
            flog = "[Voice]"
            fileID = msg['voice']['file_id']
        elif content_type == 'sticker':
            flog = "[Sticker]"
            fileID = msg['sticker']['file_id']
        if flog != "":
            if 'caption' in msg:
                flog += "Caption: {0} FileID: {1}".format(msg['caption'], fileID)
            else:
                flog += "FileID: {0}".format(fileID)
            self.logger.info(flog)
        return
