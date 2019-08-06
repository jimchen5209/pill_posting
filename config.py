#!/usr/bin/env python

from __future__ import print_function

import json
import logging
from typing import List


class Config:
    __template = {
        "//TOKEN": "Insert your telegram bot token here.",
        "TOKEN": "",
        "//Channels": "A list of channels,format:"
                      + "[{''channel'':[channel_id],''owners'':[user_id],''groups'':[group_id]}]",
        "Channels": [{"channel": -1, "owners": [], "groups": []}, ],
        "//admin_groups": "A list of admin groups.",
        "Admin_groups": [-1],
        "//Admin": "BotAdmin",
        "Admin": -1,
        "//MongoDB": "MongoDB Config, if you hosted on the same machine and didn't change port, leave it default.",
        "MongoDB": {
            "ip": "localhost",
            "port": 27017,
            "name": "PillPosting"
        },
        "//Debug": "If true,raw debug info will be logged into -debug.log file",
        "Debug": False
    }

    def __init__(self, testing=False):
        self.__logger = logging.getLogger("Config")
        logging.basicConfig(level=logging.INFO)
        self.__logger.info("Loading Config...")
        if testing:
            self.__logger.info("Testing mode detected, using testing config.")
            self.__configRaw = self.__template
        else:
            try:
                with open('./config.json', 'r') as fs:
                    self.__configRaw = json.load(fs)
            except FileNotFoundError:
                self.__logger.error(
                    "Can't load config.json: File not found.")
                self.__logger.info("Generating empty config...")
                self.__configRaw = self.__template
                self.__save_config()
                self.__logger.error("Fill your config and try again.")
                exit()
            except json.decoder.JSONDecodeError as e1:
                self.__logger.error("Can't load config.json: JSON decode error:{0}".format(str(e1.args)))
                self.__logger.error("Check your config format and try again.")
                exit()
        for pra in self.__template:
            if pra not in self.__configRaw:
                self.__configRaw[pra] = self.__template[pra]
                self.__save_config()
        self.TOKEN = self.__configRaw["TOKEN"]
        self.ChannelsRaw = self.__configRaw["Channels"]
        self.Admin_groups = self.__configRaw["Admin_groups"]
        self.Debug = self.__configRaw["Debug"]
        self.MongoDB = MongoDB(self.__configRaw['MongoDB']["ip"], self.__configRaw['MongoDB']["port"],
                               self.__configRaw['MongoDB']["name"])

    def update_channel(self, target_channel: int, data_type: str, data: List[int]):
        if data_type not in ['owners', 'groups']:
            raise SyntaxError("UnSupported data type")
        channel = {}
        for i in self.ChannelsRaw:
            if i['channel'] == target_channel:
                channel = i
                break
        if channel == {}:
            return False
        self.ChannelsRaw.remove(channel)
        channel[data_type] = data
        self.ChannelsRaw.append(channel)
        self.__configRaw['Channels'] = self.ChannelsRaw
        self.__save_config()
        return True

    def add_channel(self, channel_id: int, owners: List[int], groups: List[int]):
        channel = {}
        for i in self.ChannelsRaw:
            if i['channel'] == channel_id:
                channel = i
        if channel == {}:
            return False
        self.ChannelsRaw.append({
            'channel': channel_id,
            'owners': owners,
            'groups': groups
        })
        self.__configRaw['Channels'] = self.ChannelsRaw
        self.__save_config()
        return True

    def remove_channel(self, target_channel: int):
        channel = {}
        for i in self.ChannelsRaw:
            if i['channel'] == target_channel:
                channel = i
        if channel == {}:
            return False
        self.ChannelsRaw.remove(channel)
        self.__configRaw['Channels'] = self.ChannelsRaw
        self.__save_config()
        return True

    def __save_config(self):
        with open('./config.json', 'w') as fs:
            json.dump(self.__configRaw, fs, indent=2)


class MongoDB:
    def __init__(self, ip: str, port: int, name: str):
        self.ip = ip
        self.port = port
        self.name = name
