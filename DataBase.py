from __future__ import print_function

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
