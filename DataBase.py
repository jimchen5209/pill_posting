from __future__ import print_function

import json
import os
from typing import Optional

from pymongo import MongoClient


class MessageData:
    def __init__(
            self,
            chat_id: str,
            message_id: str,
            original_message_id: str,
            target_channel: str,
            original_chat_id: str
    ):
        self.chat_id = chat_id
        self.message_id = message_id
        self.original_message_id = original_message_id
        self.target_channel = target_channel
        self.original_chat_id = original_chat_id


class Mongo:
    __cached = {}

    def __init__(self, ip: str, port: int, dbname: str):
        self.__mongo = MongoClient(ip, port)
        self.__db = self.__mongo[dbname]
        self.__post_id = self.__db["post_id"]
        self.__post_classes = self.__db["post_classes"]
        # merge post_classes
        if os.path.isfile("./post_classes.json"):
            print("Old post classes file found. Import it to mongoDB?")
            print("Will overwrite the collection \"post_classes\" under \"{0}\"".format(dbname))
            answer = input("[y/N]").lower()
            if answer == 'y':
                print("Load post classes...")
                with open('./post_classes.json', 'r', encoding='UTF-8') as fs:
                    post_classes = json.load(fs)
                print("Dropping \"post_classes\" under \"{0}\"...".format(dbname))
                self.__post_classes.drop()
                print("Converting data...")
                new_data = []
                for i in post_classes:
                    for j in post_classes[i]:
                        new_data.append({"chat_id": i, "message_id": j, "data": post_classes[i][j]})
                print("Importing data to mongoDB...")
                self.__post_classes.insert_many(new_data)
                if not os.path.isdir("old_data"):
                    os.mkdir("old_data")
                os.rename("./post_classes.json", "./old_data/post_classes.json")
                print("Imported {0} data(s) to mongoDB.".format(str(len(new_data))))
        # merge post_id
        if os.path.isfile("./post_id.json"):
            print("Old post id file found. Import it to mongoDB?")
            print("Will overwrite the collection \"post_id\" under \"{0}\"".format(dbname))
            answer = input("[y/N]").lower()
            if answer == 'y':
                print("Load post id...")
                with open('./post_id.json', 'r', encoding='UTF-8') as fs:
                    post_id = json.load(fs)
                print("Dropping \"post_id\" under \"{0}\"...".format(dbname))
                self.__post_id.drop()
                print("Converting data...")
                new_data = []
                for i in post_id:
                    for j in post_id[i]:
                        if len(post_id[i][j]) != 0:
                            for k in post_id[i][j]:
                                new_data.append({"chat_id": i, "message_id": j, "data": k})
                print("Importing data to mongoDB...")
                self.__post_id.insert_many(new_data)
                if not os.path.isdir("old_data"):
                    os.mkdir("old_data")
                os.rename("./post_id.json", "./old_data/post_id.json")
                print("Imported {0} data(s) to mongoDB.".format(str(len(new_data))))

    def get_message_data(self, chat_id: str, message_id: str) -> Optional[MessageData]:
        if chat_id in self.__cached:
            if message_id in self.__cached[chat_id]:
                return self.__cached[chat_id][message_id]
        data = self.__post_classes.find_one({'chat_id': chat_id, "message_id": message_id})
        if data:
            data_to_return = MessageData(
                chat_id,
                message_id,
                data['data']['origmid'],
                data['data']['channel'],
                data['data']['origid']
            )
            if chat_id not in self.__cached:
                self.__cached[chat_id] = {
                    message_id: data_to_return
                }
            else:
                self.__cached[chat_id][message_id] = data_to_return
            return data_to_return

    def add_message_data(self,
                         chat_id: str,
                         message_id: str,
                         target_channel: str,
                         original_chat_id: str,
                         original_message_id: str
                         ):
        data_to_cache = MessageData(chat_id, message_id, original_message_id, target_channel, original_chat_id)
        if chat_id not in self.__cached:
            self.__cached[chat_id] = {
                message_id: data_to_cache
            }
        else:
            self.__cached[chat_id][message_id] = data_to_cache
        self.__post_classes.insert_one({
            "chat_id": chat_id,
            "message_id": message_id,
            "data": {
                "origmid": original_message_id,
                "channel": target_channel,
                "origid": original_chat_id
            }
        })

    def append_message_queue(self, chat_id: str, message_id: str, message: dict):
        self.__post_classes.insert_one({
            "chat_id": chat_id,
            "message_id": message_id,
            "data": message
        })

    def get_message_queues(self, chat_id: str, message_id: str) -> list:
        data = []
        queues = self.__post_id.find({"chat_id": chat_id, "message_id": message_id})
        count = int(queues.count())
        while count > 0:
            data.append(queues.next()[data])
            count -= 1
        return data

    def purge_message_queue(self, chat_id: str, message_id: str):
        self.__post_id.delete_many({"chat_id": chat_id, "message_id": message_id})
