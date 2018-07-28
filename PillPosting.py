import sys
import time
import telepot
import telepot.aio
import asyncio
import urllib
import urllib.request
import os
import io
import json
from telepot.aio.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

print("[Info] Starting Pill Posting")
#Config
print("[Info] Loading config...")
try:
    if sys.argv[1] == 'test':
        configraw = {
            "//TOKEN": "Insert your telegram bot token here.",
            "TOKEN": "",
            "//Channels": "A list of channels,format:[{''channel'':''<channel username>'',''owners'':[userid],''groups'':[groupid]}]",
            "Channels": [{"channel":"","owners":[0],"groups":[-1]}],
            "//admin_groups":"A list of admin groups.",
            "Admin_groups": [-1],
            "//Debug": "If true,raw debug info will be logged into -debug.log file",
            "Debug": True 
        }
    else:
        raise SyntaxError("Invaild command santax: {0}".format(sys.argv[1]))
except IndexError:
    try:
        with open('./config.json', 'r') as fs:
            configraw = json.load(fs)
    except FileNotFoundError:
        print(
            "[Error] Can't load config.json: File not found.\n[Info] Generating empty config...")
        with open('./config.json', 'w') as fs:
            configraw = {
                "//TOKEN": "Insert your telegram bot token here.",
                "TOKEN": "",
                "//Channels": "A list of channels,format:[{''channel'':''<channel username>'',''owners'':[userid],''groups'':[groupid]}]",
                "Channels": [{"channel":"","owners":[],"groups":[]},],
                "//admin_groups":"A list of admin groups.",
                "Admin_groups": [-1],
                "//Debug": "If true,raw debug info will be logged into -debug.log file",
                "Debug": False 

            }
            json.dump(configraw, fs, indent=2)
        print("\n[Info] Fill your config and try again.")
        exit()
    except json.decoder.JSONDecodeError as e1:
        print("[Error] Can't load config.json: JSON decode error:",
              e1.args, "\n\n[Info] Check your config format and try again.")
        exit()


class config:
    TOKEN = configraw['TOKEN']
    Debug = configraw["Debug"]
    Channels = configraw["Channels"]
    Admin_groups = configraw["Admin_groups"]


class Datas:
    channels = {}
    owners = {}
    groups = {}
    def __init__(self):
        for i in config.Channels:
            self.channels[i['channel']] = {"title": botwoasync.getChat(i['channel'])['title'], "owners": i['owners'], 'groups': i['groups']}
            for j in i['owners']:
                if j not in self.owners:
                    self.owners[j] = [i['channel']]
                else:
                    self.owners[j].append(i['channel'])
            for j in i['groups']:
                if j not in self.groups:
                    self.groups[j] =  [i['channel']]
                else:
                    self.groups[j].append(i['channel'])
    async def updateTitle(self, channel, new_title):
        old = self.channels[channel]['title']
        self.channels[channel]['title'] = new_title
        for i in config.Admin_groups:
            dre = await bot.sendMessage(i,"{0} 已更改標題至 {1}".format(old, new_title))
            logger.log('[Debug] Raw sent message: {0}'.format(str(dre)))

replyorg = {}


if os.path.isfile('./post_classes.json'):
    with open('./post_classes.json','r') as fs:
        post_classes = json.load(fs)
else:
    post_classes = {}


def write_PC():
    with open('./post_classes.json', 'w') as fs:
        json.dump(post_classes, fs, indent=2)


if os.path.isfile('./post_id.json'):
    with open('./post_id.json', 'r') as fs:
        post_id = json.load(fs)
else:
    post_id = {}


def write_PI():
    with open('./post_id.json', 'w') as fs:
        json.dump(post_id, fs, indent=2)


async def on_chat_message(msg):
    global replyorg
    global post_id
    global post_classes
    try:
        tmp = msg['edit_date']
    except KeyError:
        edited = False
    else:
        edited = True
    content_type, chat_type, chat_id = telepot.glance(msg)
    await logger.logmsg(msg)
    if chat_type == 'private':
        if chat_id in data.owners:
            try:
                reply_to = msg['reply_to_message']
            except KeyError:
                if content_type == "text":
                    if msg['text'] == '/start':
                        dre = await bot.sendMessage(chat_id, '您是管理員,您將會收到其他用戶傳給我的訊息,您可以管理這些訊息並選擇要不要轉寄到頻道\n\n您可以將轉寄的頻道為 ' +
                                              str(data.owners[chat_id]), reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        smsg = '您可以轉寄的頻道:\n\n'
                        for i in data.owners[chat_id]:
                            smsg += '    {0} {1}\n'.format(
                                data.channels[i]['title'], i)
                        dre = await bot.sendMessage(chat_id, smsg, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        smsg = await listchannel(chat_id,msg,False)
                        dre = await bot.sendMessage(chat_id, smsg, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        return
                    if msg['text'].startswith('/list'):
                        if msg['text'] == '/list -a':
                            smsg = await listchannel(chat_id, msg, True)
                        else:
                            smsg = await listchannel(chat_id, msg, False)
                        dre = await bot.sendMessage(chat_id, smsg,parse_mode = 'html', disable_web_page_preview=  True, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        return
                markup = choose_channel()
                dre = await bot.sendMessage(
                    chat_id, '請選擇您要投稿的頻道', reply_markup=markup, reply_to_message_id=msg['message_id'])
                logger.log("[Debug] Raw sent data:"+str(dre))
                return
            else:
                if content_type == "text":
                    if msg['text'] == '/start':
                        dre = await bot.sendMessage(chat_id, '您是管理員,您將會收到其他用戶傳給我的訊息,您可以管理這些訊息並選擇要不要轉寄到頻道', reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        smsg = '您可以轉寄的頻道:\n\n'
                        for i in data.owners[chat_id]:
                            smsg += '    {0} {1}\n'.format(
                                data.channels[i]['title'], i)
                        dre = await bot.sendMessage(chat_id, smsg, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        smsg = await listchannel(chat_id,msg,False)
                        dre = await bot.sendMessage(chat_id, smsg, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        return
                    if msg['text'].startswith('/list'):
                        if msg['text'] == '/list -a':
                            smsg = await listchannel(chat_id, msg, True)
                        else:
                            smsg = await listchannel(chat_id, msg, False)
                        dre = await bot.sendMessage(chat_id, smsg,parse_mode = 'html', disable_web_page_preview= True, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        return
                    if str(chat_id) not in post_classes:
                        post_classes[str(chat_id)] = {}
                    write_PC()
                    if msg['text'] == '/action':
                        if str(reply_to['message_id']) not in post_classes[str(chat_id)]:
                            dre = await bot.sendMessage(
                                chat_id, '我不知道此訊息要投到哪個頻道，將重新投稿', reply_to_message_id=reply_to['message_id'])
                            logger.log("[Debug] Raw sent data:"+str(dre))
                            markup = choose_channel()
                            dre = await bot.sendMessage(
                                chat_id, '請選擇您要投稿的頻道', reply_markup=markup, reply_to_message_id=reply_to['message_id'])
                            logger.log("[Debug] Raw sent data:"+str(dre))
                            return
                        if chat_id in data.channels[post_classes[str(chat_id)][str(reply_to['message_id'])]['channel']]['owners']:
                            markup = inlinekeyboardbutton(post_classes[str(chat_id)][str(reply_to['message_id'])]['channel'])
                            dre = await bot.sendMessage(
                                chat_id, '你想要對這信息做甚麼', reply_markup=markup, reply_to_message_id=reply_to['message_id'])
                            logger.log("[Debug] Raw sent data:"+str(dre))
                            post_id[post_classes[str(chat_id)][str(reply_to['message_id'])]
                                    ['origid']][post_classes[str(chat_id)][str(reply_to['message_id'])]['origmid']].append(dre)
                            write_PI()
                            return
                        else:
                            markup = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(
                                    text='重新投稿', callback_data='posting')],
                                [InlineKeyboardButton(
                                    text='取消', callback_data='cancel')],
                            ])
                            dre = await bot.sendMessage(
                                chat_id, '您不是 {0} 的頻道管理員'.format(data.channels[post_classes[str(chat_id)][str(reply_to['message_id'])]['channel']]['title']), reply_markup=markup, reply_to_message_id=msg['message_id'])
                            logger.log("[Debug] Raw sent data:"+str(dre))
                            return
                    elif msg['text'].find('#markassent') != -1:
                        await markAsSent(chat_id, msg, reply_to)
                        return
                    elif msg['text'] == '#markascancelled':
                        await markAsCancelled(chat_id, msg, reply_to)
                        return
                    else:
                        try:
                            reply_to_id = reply_to['forward_from']['id']
                        except KeyError:
                            markup = choose_channel()
                            dre = await bot.sendMessage(
                                chat_id, '請選擇您要投稿的頻道', reply_markup=markup, reply_to_message_id=msg['message_id'])
                            logger.log("[Debug] Raw sent data:"+str(dre))
                        else:
                            if reply_to_id == chat_id or reply_to_id == bot_me.id:
                                markup = choose_channel()
                                dre = await bot.sendMessage(
                                    chat_id, '請選擇您要投稿的頻道\n\n(此訊息無法被回覆)', reply_markup=markup, reply_to_message_id=msg['message_id'])
                                logger.log("[Debug] Raw sent data:"+str(dre))
                                return
                            else:
                                markup = InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(
                                        text='投稿', callback_data='posting')],
                                    [InlineKeyboardButton(
                                        text='回覆訊息擁有者(可能會失敗)', callback_data='Reply')],
                                    [InlineKeyboardButton(
                                        text='取消', callback_data='cancel')],
                                ])
                                replyorg[msg['message_id']] = msg
                                dre = await bot.sendMessage(
                                    chat_id, '你想要做甚麼?', reply_markup=markup, reply_to_message_id=msg['message_id'])
                                logger.log("[Debug] Raw sent data:"+str(dre))

                else:
                    try:
                        reply_to_id = reply_to['forward_from']['id']
                    except KeyError:
                        markup = choose_channel()
                        dre = await bot.sendMessage(
                            chat_id, '請選擇您要投稿的頻道', reply_markup=markup, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        return
                    else:
                        if reply_to_id == chat_id or reply_to_id == bot_me.id:
                            markup = choose_channel()
                            dre = await bot.sendMessage(
                                chat_id, '請選擇您要投稿的頻道\n\n(此訊息無法被回覆)', reply_markup=markup, reply_to_message_id=msg['message_id'])
                            logger.log("[Debug] Raw sent data:"+str(dre))
                            return
                        else:
                            markup = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(
                                    text='投稿', callback_data='posting')],
                                [InlineKeyboardButton(
                                    text='回覆訊息擁有者(可能會失敗)', callback_data='Reply')],
                            ])
                            replyorg[msg['message_id']] = msg
                            dre = await bot.sendMessage(
                                chat_id, '你想要做甚麼?', reply_markup=markup, reply_to_message_id=msg['message_id'])
                            logger.log("[Debug] Raw sent data:"+str(dre))
        else:
            fuser = await bot.getChatMember(chat_id, msg['from']['id'])
            fnick = fuser['user']['first_name']
            try:
                fnick = fnick + ' ' + fuser['user']['last_name']
            except KeyError:
                pass
            try:
                fnick = fnick + "@" + fuser['user']['username']
            except KeyError:
                pass
            if edited:
                for i in data.channels[post_classes[str(chat_id)][str(msg['message_id'])]['channel']]['owners']:
                    dre = await bot.sendMessage(i, fnick + "編輯了訊息")
                    logger.log("[Debug] Raw sent data:"+str(dre))
                    dre = await bot.forwardMessage(i, chat_id, msg['message_id'])
                    logger.log("[Debug] Raw sent data:"+str(dre))
                for i in config.Admin_groups:
                    dre = await bot.sendMessage(i, fnick + "編輯了訊息")
                    logger.log("[Debug] Raw sent data:"+str(dre))
                    dre = await bot.forwardMessage(i, chat_id, msg['message_id'])
                    logger.log("[Debug] Raw sent data:"+str(dre))
                dre = await bot.sendMessage(chat_id, '您的訊息已經提交審核，請耐心等候', reply_to_message_id=msg['message_id'])
                logger.log("[Debug] Raw sent data:"+str(dre))
                return
            if content_type == "text":
                if msg['text'] == '/start':
                    dre = await bot.sendMessage(chat_id, '歡迎使用投稿系統,您傳給我的任何訊息都會被轉寄給管理員,管理員可以選擇要不要轉寄到頻道', reply_to_message_id=msg['message_id'])
                    logger.log("[Debug] Raw sent data:"+str(dre))
                    smsg = await listchannel(chat_id, msg, False)
                    dre = await bot.sendMessage(chat_id, smsg, reply_to_message_id=msg['message_id'])
                    logger.log("[Debug] Raw sent data:"+str(dre))
                    return
                if msg['text'] == '/list':
                    smsg = await listchannel(chat_id, msg, False)
                    dre = await bot.sendMessage(chat_id, smsg,parse_mode = 'html', disable_web_page_preview= True, reply_to_message_id=msg['message_id'])
                    logger.log("[Debug] Raw sent data:"+str(dre))
                    return
            markup = choose_channel()
            dre = await bot.sendMessage(
                chat_id, '請選擇您要投稿的頻道', reply_markup=markup, reply_to_message_id=msg['message_id'])
            logger.log("[Debug] Raw sent data:"+str(dre))
            return
    elif chat_type == 'group' or chat_type == 'supergroup':
        if chat_id in list(data.groups)+config.Admin_groups:
            if content_type == 'new_chat_member'  :
                if msg['new_chat_member']['id'] == bot_me.id:
                    if chat_id in config.Admin_groups:
                        dre = await bot.sendMessage(chat_id, 
                        '本群組為管理群組，所有投稿訊息都會被轉到這裡\n\n本群接受所有投稿，如果您要在這裡投稿，請在要投稿的訊息並附上 #投稿\n請注意： #投稿 提交的優先度為被回覆的訊息>直接帶有 #投稿 的訊息'+
                        '如果要在本群審核訊息或直接操作訊息，請回想要被操作的訊息並打 /action')
                        logger.log("[Debug] Raw sent data:"+str(dre))
                    else:
                        dre = await bot.sendMessage(chat_id, '歡迎使用投稿系統，如果您要在這裡投稿，請在要投稿的訊息並附上 #投稿\n請注意： #投稿 提交的優先度為被回覆的訊息>直接帶有 #投稿 的訊息')
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        smsg = await listonlybyself(chat_id,msg)
                        dre = await bot.sendMessage(chat_id, smsg, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                    smsg = await listchannel(chat_id, msg, False)
                    smsg += '\n若要投稿到其他頻道請私訊我'
                    dre = await bot.sendMessage(chat_id, smsg, reply_to_message_id=msg['message_id'])
                    logger.log("[Debug] Raw sent data:"+str(dre))
            #command_detect
            
            if edited == False:
                if content_type == 'text':
                    if str(chat_id) not in post_classes:
                        post_classes[str(chat_id)] = {}
                    cmd = msg['text'].split()
                    if cmd[0] == '/start' or cmd[0] == '/start@' + bot_me.username:
                        if chat_id in config.Admin_groups:
                            dre = await bot.sendMessage(chat_id,
                                                        '本群組為管理群組，所有投稿訊息都會被轉到這裡\n\n本群接受所有投稿，如果您要在這裡投稿，請在要投稿的訊息並附上 #投稿\n請注意： #投稿 提交的優先度為被回覆的訊息>直接帶有 #投稿 的訊息' +
                                                        '如果要在本群審核訊息或直接操作訊息，請回想要被操作的訊息並打 /action')
                            logger.log("[Debug] Raw sent data:"+str(dre))
                        else:
                            dre = await bot.sendMessage(chat_id, '歡迎使用投稿系統，如果您要在這裡投稿，請在要投稿的訊息並附上 #投稿\n請注意： #投稿 提交的優先度為被回覆的訊息>直接帶有 #投稿 的訊息')
                            logger.log("[Debug] Raw sent data:"+str(dre))
                            smsg = await listonlybyself(chat_id, msg)
                            dre = await bot.sendMessage(chat_id, smsg, reply_to_message_id=msg['message_id'])
                            logger.log("[Debug] Raw sent data:"+str(dre))
                        smsg = await listchannel(chat_id, msg, False)
                        smsg += '\n若要投稿到其他頻道請私訊我'
                        dre = await bot.sendMessage(chat_id, smsg, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                    elif cmd[0] == '/action' or cmd[0] == '/action@' + bot_me.username:
                        if 'reply_to_message' in msg:
                            reply_to = msg['reply_to_message']
                            if str(reply_to['message_id']) not in post_classes[str(chat_id)]:
                                dre = await bot.sendMessage(
                                    chat_id, '我不知道此訊息要投到哪個頻道,將重新投稿', reply_to_message_id=reply_to['message_id'])
                                logger.log("[Debug] Raw sent data:"+str(dre))
                                await groupinline(msg, reply_to['message_id'], chat_id)
                                return
                            if msg['from']['id'] in data.channels[post_classes[str(chat_id)][str(reply_to['message_id'])]['channel']]['owners']:
                                markup = inlinekeyboardbutton(post_classes[str(chat_id)][str(reply_to['message_id'])]['channel'])
                                dre = await bot.sendMessage(
                                    chat_id, '你想要對這信息做甚麼', reply_markup=markup, reply_to_message_id=reply_to['message_id'])
                                logger.log("[Debug] Raw sent data:"+str(dre))
                                post_id[post_classes[str(chat_id)][str(reply_to['message_id'])]['origid']
                                        ][post_classes[str(chat_id)][str(reply_to['message_id'])]['origmid']].append(dre)
                                write_PI()
                            else:
                                dre = await bot.sendMessage(
                                    chat_id, '您不是 {0} 的頻道管理員'.format(data.channels[post_classes[str(chat_id)][str(reply_to['message_id'])]['channel']]['title']), reply_to_message_id=msg['message_id'])
                                logger.log("[Debug] Raw sent data:"+str(dre))
                        return
                    elif cmd[0]== '/list' or cmd[0]== '/list@' + bot_me.username:
                        try:
                            cmd[1]
                        except IndexError:
                            if chat_id in config.Admin_groups:
                                smsg = await listchannel(chat_id, msg, False)
                            else:
                                smsg = await listonlybyself(chat_id, msg)
                        else:
                            if cmd[1] == '-a' and (chat_id not in config.Admin_groups):
                                smsg = await listchannel(chat_id,msg,False)
                            elif cmd[1] == '-a' and chat_id in config.Admin_groups:
                                smsg = await listchannel(chat_id,msg,True)
                            else:
                                if chat_id in config.Admin_groups:
                                    smsg = await listchannel(chat_id, msg, False)
                                else:
                                    smsg = await listonlybyself(chat_id, msg)
                        
                        dre = await bot.sendMessage(chat_id, smsg,parse_mode = 'html', disable_web_page_preview= True,disable_notification= True, reply_to_message_id=msg['message_id'])
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        return
                    elif msg['text'].find('#markassent') != -1:
                        if 'reply_to_message' in msg:
                            reply_to = msg['reply_to_message']
                            await markAsSent(chat_id, msg, reply_to)
                        return
                    elif msg['text'].find('#markascancelled') != -1:
                        if 'reply_to_message' in msg:
                            reply_to = msg['reply_to_message']
                            await markAsCancelled(chat_id, msg, reply_to)
                        return
                    if msg['text'].find('#投稿') != -1:
                        if 'reply_to_message' in msg:
                            reply_to = msg['reply_to_message']
                            await groupinline(msg, reply_to['message_id'], chat_id)
                        else:
                            await groupinline(msg, msg['message_id'], chat_id)
                        
                else:
                    try:
                        caption = msg['caption']
                    except KeyError:
                        pass
                    else:
                        if caption.find('#投稿') != -1:
                            try:
                                reply_to = msg['reply_to_message']
                            except KeyError:
                                await groupinline(msg, msg['message_id'], chat_id)
                            else:
                                await groupinline(msg, reply_to['message_id'], chat_id)

        else:
            #Auto leave group
            dre = await bot.sendMessage(chat_id, '我不適用於此群組')
            logger.log("[Debug] Raw sent data:"+str(dre))
            logger.clog('[Info]['+str(msg['message_id'])+'] I left the ' +
                chat_type+':'+msg['chat']['title']+'('+str(chat_id)+')')
            await bot.leaveChat(chat_id)
    elif chat_type == 'channel':
        try:
            channel_username = '@{0}'.format(msg['chat']['username'])
        except KeyError:
            pass
        else:
            if channel_username in data.channels:
                if content_type == 'new_chat_title':
                    await data.updateTitle(channel_username,msg['new_chat_title'])
    return


async def listonlybyself(chat_id, msg):
    smsg = '本群管轄的頻道:\n\n'
    for i in data.groups[chat_id]:
        smsg += '    {0} {1}\n'.format(
            data.channels[i]['title'], i)
    return smsg

async def listchannel(chat_id,msg,list_admin):
    smsg = '本bot管轄的頻道列表:\n\n'
    for i in data.channels:
        adminList = ''
        if list_admin:
            for j in data.channels[i]['owners']:
                try:
                    fuser = await bot.getChatMember(config.Admin_groups[0],j)
                    fnick = fuser['user']['first_name']
                    if 'last_name' in fuser['user']:
                        fnick = fnick + ' ' + fuser['user']['last_name']
                    adminList += '<a href="tg://user?id={1}">{0}</a> '.format(fnick,j)
                except telepot.exception.TelegramError:
                    adminList += str(j) + ' '
        smsg += '    {0} {1}'.format(
            data.channels[i]['title'], i)
        if list_admin:
            smsg += '\n        管理員列表：' + adminList
        smsg += "\n"
    return smsg

async def markAsSent(chat_id, msg, reply_to):
    try:
        post_class = post_classes[str(chat_id)][str(reply_to['message_id'])]
    except KeyError:
        dre = await bot.sendMessage(chat_id, "操作失敗，此訊息沒有投稿紀錄",reply_to_message_id=msg['message_id'])
        logger.log("[Debug] Raw sent data: {0}".format(str(dre)))
        return
    for i in post_id[post_class['origid']][post_class['origmid']]:
        try:
            msg_idf = telepot.message_identifier(i)
            await bot.editMessageText(msg_idf, '訊息已被其他管理員轉寄至頻道\n\n若想要再次對訊息操作請回復訊息並打 /action')
        except telepot.exception.TelegramError as e1:
            logger.clog("[ERROR][MAS] Something went wrong: {0}".format(str(e1.args)))
    post_id[post_class['origid']][post_class['origmid']].clear()
    write_PI()
    dre = await bot.sendMessage(chat_id, "操作已完成", reply_to_message_id=msg['message_id'])
    logger.log("[Debug] Raw sent data: {0}".format(str(dre)))
    return

async def markAsCancelled(chat_id, msg, reply_to):
    try:
        post_class = post_classes[str(chat_id)][str(reply_to['message_id'])]
    except KeyError:
        dre = await bot.sendMessage(chat_id, "操作失敗，此訊息沒有投稿紀錄",reply_to_message_id=msg['message_id'])
        logger.log("[Debug] Raw sent data: {0}".format(str(dre)))
        return
    for i in post_id[post_class['origid']][post_class['origmid']]:
        try:
            msg_idf = telepot.message_identifier(i)
            await bot.editMessageText(msg_idf, '操作已被其他管理員取消\n\n若想要再次對訊息操作請回復訊息並打 /action')
        except telepot.exception.TelegramError as e1:
            logger.clog("[ERROR][MAC] Something went wrong: {0}".format(str(e1.args)))
    post_id[post_class['origid']][post_class['origmid']].clear()
    write_PI()
    dre = await bot.sendMessage(chat_id, "操作已完成",reply_to_message_id=msg['message_id'])
    logger.log("[Debug] Raw sent data: {0}".format(str(dre)))
    return

def inlinekeyboardbutton(channel):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='直接轉寄到 {0}'.format(data.channels[channel]['title']), callback_data='FTC')],
        [InlineKeyboardButton(
            text='匿名轉寄到 {0}'.format(data.channels[channel]['title']), callback_data='PFTC')],
        [InlineKeyboardButton(
            text='取消', callback_data='ecancel')],
    ])
    return(markup)

def choose_channel():
    keyboard = []
    for i in data.channels:
        keyboard.append([InlineKeyboardButton(
            text=data.channels[i]['title'], callback_data='post:'+i)])
    keyboard.append(
        [InlineKeyboardButton(
            text='取消', callback_data='cancel')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return(markup)

async def groupinline(msg, id, chat_id):
    if chat_id in config.Admin_groups:
        keyboard = []
        for i in data.channels:
            keyboard.append([InlineKeyboardButton(
                text=data.channels[i]['title'], callback_data='grouppost:'+i+':'+str(id))])
        keyboard.append(
            [InlineKeyboardButton(
                text='取消', callback_data='cancel')])
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        dre = await bot.sendMessage(
            chat_id, '請選擇您要投稿的頻道', reply_markup=markup, reply_to_message_id=id)
        logger.log("[Debug] Raw sent data:"+str(dre))
        return
    elif len(data.groups[chat_id]) == 1:
        dre = await bot.sendMessage(
            chat_id, '本群只管轄一個頻道', reply_to_message_id=id)
        logger.log("[Debug] Raw sent data:"+str(dre))
        await groupinlinefinal(chat_id, msg, id, dre, data.groups[chat_id][0])
        return
    else:
        keyboard = []
        for i in data.groups[chat_id]:
            keyboard.append([InlineKeyboardButton(
                text=data.channels[i]['title'], callback_data='grouppost:'+i+':'+id)])
        keyboard.append(
            [InlineKeyboardButton(
                text='取消', callback_data='cancel')])
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        dre = await bot.sendMessage(
            chat_id, '請選擇您要投稿的頻道', reply_markup=markup, reply_to_message_id=id)
        logger.log("[Debug] Raw sent data:"+str(dre))
        return

async def groupinlinefinal(chat_id, msg, id, mwik, channel):
    global post_classes
    global post_id
    if str(chat_id) in post_classes:
        post_classes[str(chat_id)][str(id)] = {"channel":channel, "origid":str(chat_id), "origmid": str(id)}
    else:
        post_classes[str(chat_id)] = {str(id): {
            "channel": channel, "origid": str(chat_id), "origmid": str(id)}}
    msg_idf = telepot.message_identifier(mwik)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='開始審核', callback_data='OWNERARRIVE')],
        [InlineKeyboardButton(
            text='{0}'.format(data.channels[channel]['title']), url="https://t.me/{0}/".format(channel[1:]))]
    ])
    gdre = await bot.editMessageText(msg_idf, '已提交此訊息給管理員，請耐心等候', reply_markup=markup)
    logger.log("[Debug] Raw sent data:"+str(gdre))
    if str(chat_id) not in post_id:
        post_id[str(chat_id)] = {str(id): []}
    else:
        post_id[str(chat_id)][str(id)] = []
    post_id[str(chat_id)][str(id)].append(gdre)
    try:
        username = msg['chat']['username']
    except KeyError:
        username = None
    string = ""
    count = 0
    for i in data.channels[channel]['owners']+config.Admin_groups:
        try:
            if chat_id == i:
                continue
            dre = await bot.forwardMessage(i, chat_id, id)
            logger.log("[Debug] Raw sent data:"+str(dre))
            if str(i) in post_classes:
                post_classes[str(i)][str(dre['message_id'])] = {
                    "channel": channel, "origid": str(chat_id), "origmid": str(id)}
            else:
                post_classes[str(i)] = {str(dre['message_id']): {
                    "channel": channel, "origid": str(chat_id), "origmid": str(id)}}
            if username == None:
                tdre = await bot.sendMessage(i, '有人在 {0} 投稿 {1}\n\n由於這是私人群組,我無法建立連結,請自行前往群組查看'.format(msg['chat']['title'], data.channels[channel]['title'])
                                            , reply_to_message_id=dre['message_id'])
                logger.log("[Debug] Raw sent data:"+str(tdre))
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text='開始審核', callback_data='OWNERARRIVE')]
                ])
                tdre = await bot.sendMessage(i, '您也可以選擇在這裡審核', reply_markup=markup, reply_to_message_id=dre['message_id'])
                logger.log("[Debug] Raw sent data:"+str(tdre))
                post_id[str(chat_id)][str(id)].append(tdre)
                if i in data.channels[channel]['owners']:
                    string += "[.](tg://user?id={0})".format(i)
                    count += 1
                    if count >= 5:
                        dre = await bot.sendMessage(chat_id, string, parse_mode="Markdown")
                        logger.log("[Debug] Raw sent data:"+str(dre))
                        string = ""
                        count = 0
            else:
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text='前往該訊息', url="https://t.me/{0}/{1}".format(username, str(gdre['message_id'])))],
                ])
                tdre = await bot.sendMessage(i, '有人在 {0} 想要投稿到 {1}'.format(msg['chat']['title'], data.channels[channel]['title']), 
                                        reply_markup=markup, reply_to_message_id=dre['message_id'])
                logger.log("[Debug] Raw sent data:"+str(tdre))
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text='開始審核', callback_data='OWNERARRIVE')]
                ])
                tdre = await bot.sendMessage(i, '您也可以選擇在這裡審核', reply_markup=markup, reply_to_message_id=dre['message_id'])
                logger.log("[Debug] Raw sent data:"+str(tdre))
                post_id[str(chat_id)][str(id)].append(tdre)
        except telepot.exception.TelegramError:
            if i in data.channels[channel]['owners']:
                try:
                    user = await bot.getChatMember(chat_id, i)
                    if user['status'] != "left":
                        markup = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(
                                text='啟用我', url="https://t.me/{0}/".format(bot_me.username))],
                        ])
                        dre = await bot.sendMessage(chat_id, 
                            '[{0}](tg://user?id={1}) 我無法傳送訊息給您，身為頻道管理員的您，請記得啟用我來接收投稿訊息'.format(user['user']['first_name'], user['user']['id']),
                            parse_mode="Markdown", reply_markup=markup)
                        logger.log("[Debug] Raw sent data:"+str(dre))
                except telepot.exception.TelegramError as e1:
                    logger.clog('[ERROR]Telegram Error occured {0} {1}'.format(str(i),str(e1.args)))
        
    if count != 0:
        dre = await bot.sendMessage(chat_id, string, parse_mode="Markdown")
        logger.log("[Debug] Raw sent data:"+str(dre))
    write_PC()
    write_PI()
    return

async def on_callback_query(msg):
    logger.log("[Debug] Raw query data:"+str(msg))
    orginal_message = msg['message']['reply_to_message']
    message_with_inline_keyboard = msg['message']
    content_type, chat_type, chat_id = telepot.glance(orginal_message)
    query_id, from_id, callbackdata = telepot.glance(msg, flavor='callback_query')
    logger.clog("["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "")+"][Info]["+str(query_id) +
                "] Callback query form "+str(from_id)+" to "+str(orginal_message['message_id'])+" :" + callbackdata)
    if callbackdata.startswith('post:'):
        # if from_id != orginal_message['from']['id']:
        #     await bot.answerCallbackQuery(
        #         query_id, text='請不要亂戳\n\n您不是指令要求者', show_alert=True)
            # return
        a = callbackdata.split(':')
        await post(chat_id, orginal_message, query_id,
                message_with_inline_keyboard, orginal_message, a[1])
        return
    if callbackdata.startswith('grouppost:'):
        # if from_id != orginal_message['from']['id']:
        #     await bot.answerCallbackQuery(
        #         query_id, text='請不要亂戳\n\n您不是指令要求者', show_alert=True)
        #     return
        a = callbackdata.split(':')
        await groupinlinefinal(chat_id, orginal_message, a[2], message_with_inline_keyboard, a[1])
        return
    if callbackdata == 'cancel':
        # if from_id != orginal_message['from']['id']:
        #     await bot.answerCallbackQuery(
        #         query_id, text='請不要亂戳\n\n您不是指令要求者', show_alert=True)
        #     return
        await cancelquery(message_with_inline_keyboard, orginal_message)
        return
    try:
        if from_id in data.owners:
            if callbackdata == 'Reply':
                await Reply(chat_id, orginal_message, query_id,
                            message_with_inline_keyboard, orginal_message)
            elif callbackdata == 'posting':
                await posting(message_with_inline_keyboard, orginal_message)
            else:
                if from_id in data.channels[post_classes[str(chat_id)][str(orginal_message['message_id'])]['channel']]['owners']:
                    if callbackdata == 'FTC':
                        await FTC(chat_id, orginal_message, query_id,
                            message_with_inline_keyboard, orginal_message)
                    elif callbackdata == 'PFTC':
                        await PFTC(chat_id, orginal_message, content_type, query_id,
                            message_with_inline_keyboard, orginal_message)
                    elif callbackdata == 'OWNERARRIVE':
                        await OWNERARRIVE(chat_id, orginal_message, query_id,
                                        message_with_inline_keyboard, orginal_message)
                    elif callbackdata == 'ecancel':
                        await ecancelquery(chat_id, message_with_inline_keyboard, orginal_message)
                else:
                    await bot.answerCallbackQuery(
                        query_id, text='請不要亂戳\n\n您不是 {0} 的管理員'.format(data.channels[post_classes[str(chat_id)][str(orginal_message['message_id'])]['channel']]['title']), show_alert=True)
        else:
            await bot.answerCallbackQuery(
                query_id, text='請不要亂戳\n\n您不是任何頻道的管理員', show_alert=True)
    except KeyError as e1:
        await bot.answerCallbackQuery(query_id, text='操作已過期\n\n{0}'.format(
            str(e1.args)), show_alert=True)
        gmsg_idf = telepot.message_identifier(
            message_with_inline_keyboard)
        await bot.editMessageText(gmsg_idf, '操作已過期\n\n{0}'.format(str(e1.args)))
    return

async def posting(mwik, original_message):
    msg_idf = telepot.message_identifier(mwik)
    markup = choose_channel()
    dre = await bot.editMessageText(
        msg_idf, '請選擇您要投稿的頻道', reply_markup=markup)
    logger.log("[Debug] Raw sent data:"+str(dre))
    pass

async def post(chat_id, msg, query_id, mwik, orginalmsg, channel):
    global post_classes
    global post_id
    if chat_id in data.channels[channel]['owners']:
        if str(chat_id) in post_classes:
            post_classes[str(chat_id)][str(msg['message_id'])] = {
                "channel": channel, "origid": str(chat_id), "origmid": str(msg['message_id'])}
        else:
            post_classes[str(chat_id)]= {str(msg['message_id']): {
                "channel": channel, "origid": str(chat_id), "origmid": str(msg['message_id'])}}
        if str(chat_id) not in post_id:
            post_id[str(chat_id)] = { str(msg['message_id']): []}
        else:
            post_id[str(chat_id)][str(msg['message_id'])] = []
        msg_idf = telepot.message_identifier(mwik)
        markup = inlinekeyboardbutton(channel)
        dre = await bot.editMessageText(
            msg_idf, '你想要對這信息做甚麼', reply_markup=markup)
        logger.log("[Debug] Raw sent data:"+str(dre))
        post_id[str(chat_id)][str(msg['message_id'])].append(dre)
    else:
        if str(chat_id) not in post_id:
            post_id[str(chat_id)] = {str(msg['message_id']):[]}
        else:
            post_id[str(chat_id)][str(msg['message_id'])] = []
        for i in data.channels[channel]['owners']+config.Admin_groups:
            try:
                dre = await bot.forwardMessage(i, chat_id, msg['message_id'])
                logger.log("[Debug] Raw sent data:"+str(dre))
                if str(i) in post_classes:
                    post_classes[str(i)][str(dre['message_id'])] = {
                        "channel": channel, "origid": str(chat_id), "origmid": str(msg['message_id'])}
                else:
                    post_classes[str(i)] = {str(dre['message_id']): {
                        "channel": channel, "origid": str(chat_id), "origmid": str(msg['message_id'])}}
                if i in data.channels[channel]['owners']:
                    markup = inlinekeyboardbutton(channel)
                    dre = await bot.sendMessage(
                        i, '你想要對這信息做甚麼', reply_markup=markup, reply_to_message_id=dre['message_id'])
                    logger.log("[Debug] Raw sent data:"+str(dre))
                    post_id[str(chat_id)][str(msg['message_id'])].append(dre)
                elif i in config.Admin_groups:
                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text='開始審核', callback_data='OWNERARRIVE')],
                    ])
                    dre = await bot.sendMessage(
                        i, '有人想投稿到 {0}'.format(data.channels[channel]['title']), reply_markup=markup, reply_to_message_id=dre['message_id'])
                    logger.log("[Debug] Raw sent data:"+str(dre))
                    post_id[str(chat_id)][str(msg['message_id'])].append(dre)
            except telepot.exception.TelegramError as e1:
                logger.clog('[ERROR]Telegram Error occured {0} {1}'.format(str(i),str(e1.args)))
        msg_idf = telepot.message_identifier(mwik)
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
            text='{0}'.format(data.channels[channel]['title']), url="https://t.me/{0}/".format(channel[1:]))]
            ])
        dre = await bot.editMessageText(msg_idf, '您的訊息已經提交審核，請耐心等候', reply_markup=markup)
        logger.log("[Debug] Raw sent data:"+str(dre))
    write_PC()
    write_PI()
    return

async def OWNERARRIVE(chat_id, msg, query_id, mwik, orginalmsg):
    markup = inlinekeyboardbutton(post_classes[str(chat_id)][str(msg['message_id'])]['channel'])
    msg_idf = telepot.message_identifier(mwik)
    await bot.editMessageText(msg_idf, '你想要對這信息做甚麼', reply_markup=markup)
    return

async def FTC(chat_id, msg, query_id, mwik, orginalmsg):
    post_class = post_classes[str(chat_id)][str(msg['message_id'])]
    channel = post_class['channel']
    post_channel = []
    try:
        dre = await bot.forwardMessage(channel, chat_id, msg['message_id'])
        logger.log("[Debug] Raw sent data:"+str(dre))
        post_channel.append([InlineKeyboardButton(
            text='{0}'.format(data.channels[channel]['title']), url="https://t.me/{0}/{1}".format(channel[1:],dre['message_id']))])
    except telepot.exception.TelegramError as e1:
        await bot.answerCallbackQuery(query_id, text='無法轉寄信息:\n\n'+str(e1.args[0]), show_alert=True)
        logger.clog('[ERROR] Unable to forward message to'+channel +' : '+str(e1.args))
        return
    markup = InlineKeyboardMarkup(inline_keyboard=post_channel)
    await bot.answerCallbackQuery(
        query_id, text='操作已完成\n\n若想要再次對訊息操作請回復訊息並打 /action', show_alert=True)
    logger.clog('[Info] Successfully forwarded message to'+channel)
    gmsg_idf = telepot.message_identifier(mwik)
    await bot.editMessageText(gmsg_idf, '操作已完成\n\n若想要再次對訊息操作請回復訊息並打 /action', reply_markup=markup)
    for i in post_id[post_class['origid']][post_class['origmid']]:
        msg_idf = telepot.message_identifier(i)
        if msg_idf != gmsg_idf:
            await bot.editMessageText(msg_idf, '訊息已被其他管理員轉寄至頻道\n\n若想要再次對訊息操作請回復訊息並打 /action', reply_markup=markup)
    post_id[post_class['origid']][post_class['origmid']].clear()
    write_PI()
    try:
        del replyorg[orginalmsg['message_id']]
    except KeyError:
        pass
    return

async def PFTC(chat_id, msg, content_type, query_id, mwik, orginalmsg):
    post_class = post_classes[str(chat_id)][str(msg['message_id'])]
    channel = post_class['channel']
    dre = {}
    try:
        if content_type == 'text':
            dre = await bot.sendMessage(channel, msg['text'])
            logger.log("[Debug] Raw sent data:"+str(dre))
        elif content_type == 'photo':
            try:
                caption = msg['caption']
            except KeyError:
                photo_array = msg['photo']
                dre = await bot.sendPhoto(
                    channel, photo_array[-1]['file_id'])
                logger.log("[Debug] Raw sent data:"+str(dre))
            else:
                photo_array = msg['photo']
                dre = await bot.sendPhoto(
                    channel, photo_array[-1]['file_id'], caption=caption)
                logger.log("[Debug] Raw sent data:"+str(dre))
        elif content_type == 'audio':
            try:
                caption = msg['caption']
            except KeyError:
                dre = await bot.sendAudio(channel, msg['audio']['file_id'])
                logger.log("[Debug] Raw sent data:"+str(dre))
            else:
                dre = await bot.sendAudio(
                    channel, msg['audio']['file_id'], caption=caption)
                logger.log("[Debug] Raw sent data:"+str(dre))
        elif content_type == 'document':
            try:
                caption = msg['caption']
            except KeyError:
                dre = await bot.sendDocument(
                    channel, msg['document']['file_id'])
                logger.log("[Debug] Raw sent data:"+str(dre))
            else:
                dre = await bot.sendDocument(
                    channel, msg['document']['file_id'], caption=caption)
                logger.log("[Debug] Raw sent data:"+str(dre))
        elif content_type == 'video':
            try:
                caption = msg['caption']
            except KeyError:
                dre = await bot.sendVideo(channel, msg['video']['file_id'])
                logger.log("[Debug] Raw sent data:"+str(dre))
            else:
                dre = await bot.sendVideo(
                    channel, msg['video']['file_id'], caption=caption)
                logger.log("[Debug] Raw sent data:"+str(dre))
        elif content_type == 'voice':
            try:
                caption = msg['caption']
            except KeyError:
                dre = await bot.sendVoice(channel, msg['voice']['file_id'])
                logger.log("[Debug] Raw sent data:"+str(dre))
            else:
                dre = await bot.sendVoice(
                    channel, msg['voice']['file_id'], caption=caption)
                logger.log("[Debug] Raw sent data:"+str(dre))
        elif content_type == 'sticker':
            dre = await bot.sendSticker(
                    channel, msg['sticker']['file_id'])
            logger.log("[Debug] Raw sent data:"+str(dre))
        else:
            dre = await bot.answerCallbackQuery(
                query_id, text='ERROR:暫不支援的信息種類', show_alert=True)
            logger.log("[Debug] Raw sent data:"+str(dre))
            logger.clog("[ERROR] Unsupported content type:"+content_type)
            return
    except telepot.exception.TelegramError as e1:
        await bot.answerCallbackQuery(query_id, text='無法轉寄信息:\n\n'+str(e1.args), show_alert=True)
        logger.clog('[ERROR] Unable to send message to'+channel +
             ' : '+str(e1.args[0]))
        return
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text='{0}'.format(data.channels[channel]['title']), url="https://t.me/{0}/{1}".format(channel[1:], dre['message_id']))]])
    await bot.answerCallbackQuery(
        query_id, text='操作已完成\n\n若想要再次對訊息操作請回復訊息並打 /action', show_alert=True)
    logger.clog('[Info] Successfully sent message to'+channel)
    gmsg_idf = telepot.message_identifier(mwik)
    await bot.editMessageText(gmsg_idf, '操作已完成\n\n若想要再次對訊息操作請回復訊息並打 /action',reply_markup=markup)
    for i in post_id[post_class['origid']][post_class['origmid']]:
        msg_idf = telepot.message_identifier(i)
        if msg_idf != gmsg_idf:
            await bot.editMessageText(msg_idf, '訊息已被其他管理員轉寄至頻道\n\n若想要再次對訊息操作請回復訊息並打 /action', reply_markup=markup)
    post_id[post_class['origid']][post_class['origmid']].clear()
    write_PI()
    try:
        del replyorg[orginalmsg['message_id']]
    except KeyError:
        pass
    return

async def Reply(chat_id, msg, query_id, mwik, orginalmsg):
    global replyorg
    try:
        reply_to_id = replyorg[orginalmsg['message_id']
                               ]['reply_to_message']['forward_from']['id']
    except KeyError as e1:
        await bot.answerCallbackQuery(query_id, text='操作已過期\n\n{0}'.format(
            str(e1.args)), show_alert=True)
        gmsg_idf = telepot.message_identifier(mwik)
        await bot.editMessageText(gmsg_idf, '操作已過期\n\n{0}'.format(str(e1.args)))
        return
    try:
        await bot.sendMessage(reply_to_id, '管理員對您信息的回覆：')
        dre = await bot.forwardMessage(reply_to_id, chat_id, msg['message_id'])
        logger.log("[Debug] Raw sent data:"+str(dre))
    except telepot.exception.TelegramError as e1:
        await bot.answerCallbackQuery(query_id, text='操作失敗\n\n{0}'.format(
            str(e1.args[0])), show_alert=True)
    else:
        await bot.answerCallbackQuery(
            query_id, text='操作已完成\n\n若想要再次對訊息操作請回復訊息並打 /action', show_alert=True)
        msg_idf = telepot.message_identifier(mwik)
        await bot.editMessageText(msg_idf, '操作已完成\n\n若想要再次對訊息操作請回復訊息並打 /action')
        del replyorg[orginalmsg['message_id']]
    return

async def cancelquery(mwik, orginalmsg):
    msg_idf = telepot.message_identifier(mwik)
    await bot.editMessageText(msg_idf, '操作已被取消\n\n若想要再次對訊息操作請回復訊息並打 /action')
    try:
        del replyorg[orginalmsg['message_id']]
    except:
        pass
    return

async def ecancelquery(chat_id, mwik, orginalmsg):
    post_class = post_classes[str(chat_id)][str(orginalmsg['message_id'])]
    gmsg_idf = telepot.message_identifier(mwik)
    await bot.editMessageText(gmsg_idf, '操作已被取消\n\n若想要再次對訊息操作請回復訊息並打 /action')
    for i in post_id[post_class['origid']][post_class['origmid']]:
        msg_idf = telepot.message_identifier(i)
        if msg_idf != gmsg_idf:
            await bot.editMessageText(msg_idf, '操作已被其他管理員取消\n\n若想要再次對訊息操作請回復訊息並打 /action')
    post_id[post_class['origid']][post_class['origmid']].clear()
    write_PI()
    try:
        del replyorg[orginalmsg['message_id']]
    except:
        pass
    return

class Log:
    logpath = "./logs/"+time.strftime("%Y-%m-%d-%H-%M-%S").replace("'", "")

    def __init__(self):
        if os.path.isdir("./logs") == False:
            os.mkdir("./logs")
        self.log(
            "[Logger] If you don't see this file currectly,turn the viewing encode to UTF-8.")
        self.log(
            "[Debug][Logger] If you don't see this file currectly,turn the viewing encode to UTF-8.")
        self.log("[Debug] Bot's TOKEN is "+config.TOKEN)

    async def logmsg(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        self.log("[Debug] Raw message:"+str(msg))
        dlog = "[" + \
            time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "")+"][Info]"
        flog = ""
        try:
            dlog += "[EDITED"+str(msg['edit_date'])+"]"
        except KeyError:
            pass
        try:
            fuser = await bot.getChatMember(chat_id, msg['from']['id'])
        except KeyError:
            fnick = "Channel Admin"
            fuserid = None
        else:
            fnick = fuser['user']['first_name']
            try:
                fnick += ' ' + fuser['user']['last_name']
            except KeyError:
                pass
            try:
                fnick += "@" + fuser['user']['username']
            except KeyError:
                pass
            fuserid = str(fuser['user']['id'])
        if chat_type == 'private':
            dlog += "[Private]"
        dlog += "["+str(msg['message_id'])+"]"
        try:
            reply_to = msg['reply_to_message']['from']['id']
        except KeyError:
            pass
        else:
            if chat_type != 'channel':
                if reply_to == bot_me.id:
                    dlog += " ( Reply to my message " + \
                        str(msg['reply_to_message']['message_id'])+" )"
                else:
                    tuser = msg['reply_to_message']['from']['first_name']
                    try:
                        tuser += ' ' + \
                            msg['reply_to_message']['from']['last_name']
                    except KeyError:
                        pass
                    try:
                        tuser += '@' + \
                            msg['reply_to_message']['from']['username']
                    except KeyError:
                        pass
                    dlog += " ( Reply to "+tuser+"'s message " + \
                        str(msg['reply_to_message']['message_id'])+" )"
            else:
                dlog += \
                    " ( Reply to " + \
                    str(msg['reply_to_message']['message_id'])+" )"
        if chat_type == 'private':
            if content_type == 'text':
                dlog += ' ' + fnick + " ( "+fuserid+" ) : " + msg['text']
            else:
                dlog += ' ' + fnick + \
                    " ( "+fuserid+" ) sent a " + content_type
        elif chat_type == 'group' or chat_type == 'supergroup':
            if content_type == 'text':
                dlog += ' ' + fnick + \
                    " ( "+fuserid+" ) in "+msg['chat']['title'] + \
                    ' ( '+str(chat_id) + ' ): ' + msg['text']
            elif content_type == 'new_chat_member':
                if msg['new_chat_member']['id'] == bot_me.id:
                    dlog += ' I have been added to ' + \
                        msg['chat']['title'] + \
                        ' ( '+str(chat_id) + ' ) by ' + \
                        fnick + " ( "+fuserid+" )"
                else:
                    tuser = msg['new_chat_member']['first_name']
                    try:
                        tuser += ' ' + msg['new_chat_member']['last_name']
                    except KeyError:
                        pass
                    try:
                        tuser += '@' + msg['new_chat_member']['username']
                    except KeyError:
                        pass
                    dlog += ' ' + tuser + ' joined the ' + chat_type + \
                        ' '+msg['chat']['title']+' ( '+str(chat_id) + ' ) '
            elif content_type == 'left_chat_member':
                if msg['left_chat_member']['id'] == bot_me.id:
                    dlog += ' I have been kicked from ' + \
                        msg['chat']['title'] + \
                        ' ( '+str(chat_id) + ' ) by ' + \
                        fnick + " ( "+fuserid+" )"
                else:
                    tuser = msg['left_chat_member']['first_name']
                    try:
                        tuser += ' ' + msg['left_chat_member']['last_name']
                    except KeyError:
                        pass
                    try:
                        tuser += '@' + msg['left_chat_member']['username']
                    except KeyError:
                        pass
                    dlog += ' ' + tuser + ' left the ' + chat_type + \
                        ' '+msg['chat']['title']+' ( '+str(chat_id) + ' ) '
            elif content_type == 'pinned_message':
                tuser = msg['pinned_message']['from']['first_name']
                try:
                    tuser += ' ' + \
                        msg['pinned_message']['from']['last_name']
                except KeyError:
                    pass
                try:
                    tuser += '@' + msg['pinned_message']['from']['username']
                except KeyError:
                    pass
                tmpcontent_type, tmpchat_type = telepot.glance(
                    msg['pinned_message'])
                if tmpcontent_type == 'text':
                    dlog += ' ' + tuser + "'s message["+str(msg['pinned_message']['message_id'])+"] was pinned to " +\
                        msg['chat']['title']+' ( '+str(chat_id) + ' ) by ' + fnick + \
                        " ( "+fuserid+" ):\n"+msg['pinned_message']['text']
                else:
                    dlog += ' ' + tuser + "'s message["+str(msg['pinned_message']['message_id'])+"] was pinned to " +\
                        msg['chat']['title'] + \
                        ' ( '+str(chat_id) + ' ) by ' + \
                        fnick + " ( "+fuserid+" )"
                    self.__log_media(tmpchat_type, msg['pinned_message'])
            elif content_type == 'new_chat_photo':
                dlog += " The photo of this "+chat_type + ' ' + \
                    msg['chat']['title']+' ( '+str(chat_id) + \
                    ' ) was changed by '+fnick + " ( "+fuserid+" )"
                flog = "[New Chat Photo]"
                photo_array = msg['new_chat_photo']
                photo_array.reverse()
                try:
                    flog = flog + "Caption = " + \
                        msg['caption'] + " ,FileID:" + \
                        photo_array[0]['file_id']
                except KeyError:
                    flog = flog + "FileID:" + photo_array[0]['file_id']
            elif content_type == 'group_chat_created':
                if msg['new_chat_member']['id'] == bot_me.id:
                    dlog += ' ' + fnick + " ( "+fuserid+" ) created a " + chat_type + ' ' + \
                        msg['chat']['title'] + \
                        ' ( '+str(chat_id) + ' ) and I was added into the group.'
            elif content_type == 'migrate_to_chat_id':
                newgp = await bot.getChat(msg['migrate_to_chat_id'])
                dlog += ' ' + chat_type + ' ' + msg['chat']['title']+' ( '+str(
                    chat_id) + ' ) was migrated to ' + newgp['type'] + ' ' + newgp['title'] + ' ('+str(newgp['id'])+')  by ' + fnick + " ( "+fuserid+" )"
            elif content_type == 'migrate_from_chat_id':
                oldgp = await bot.getChat(msg['migrate_from_chat_id'])
                dlog += ' ' + chat_type + ' ' + msg['chat']['title']+' ( '+str(
                    chat_id) + ' ) was migrated from ' + oldgp['type'] + ' ' + oldgp['title'] + ' ('+str(oldgp['id'])+')  by ' + fnick + " ( "+fuserid+" )"
            elif content_type == 'delete_chat_photo':
                dlog += " The photo of this "+chat_type + ' ' + \
                    msg['chat']['title']+' ( '+str(chat_id) + \
                    ' ) was deleted by '+fnick + " ( "+fuserid+" )"
            elif content_type == 'new_chat_title':
                dlog += " The title of this "+chat_type + " was changed to " + \
                    msg['new_chat_title']+" by "+fnick + " ( "+fuserid+" )"
            else:
                dlog += ' ' + fnick + \
                    " ( "+fuserid+" ) in "+msg['chat']['title'] + \
                    ' ( '+str(chat_id) + ' ) sent a ' + content_type
        elif chat_type == 'channel':
            if content_type == 'text':
                dlog += ' ' + fnick
                if fuserid:
                    dlog += " ( "+fuserid+" )"
                dlog += ' ' + " in channel " + \
                    msg['chat']['title'] + \
                    ' ( '+str(chat_id) + ' ): ' + msg['text']
            elif content_type == 'new_chat_photo':
                dlog += " The photo of this "+chat_type+"" + ' ' + \
                    msg['chat']['title'] + \
                    ' ( '+str(chat_id) + ' ) was changed by '+fnick
                if fuserid:
                    dlog += " ( "+fuserid+" )"
                flog = "[New Chat Photo]"
                photo_array = msg['new_chat_photo']
                photo_array.reverse()
                try:
                    flog = flog + "Caption = " + \
                        msg['caption'] + " ,FileID:" + \
                        photo_array[0]['file_id']
                except KeyError:
                    flog = flog + "FileID:" + photo_array[0]['file_id']
            elif content_type == 'pinned_message':
                tmpcontent_type, tmpchat_type, tmpchat_id = telepot.glance(
                    msg['pinned_message'])
                if tmpcontent_type == 'text':
                    dlog += ' ' + "A message["+str(msg['pinned_message']['message_id'])+"] was pinned to " +\
                        msg['chat']['title'] + \
                        ' ( '+str(chat_id) + ' ) by :\n' + \
                        msg['pinned_message']['text']
                else:
                    dlog += ' ' "A message["+str(msg['pinned_message']['message_id'])+"] was pinned to " +\
                        msg['chat']['title'] + \
                        ' ( '+str(chat_id) + ' ) '
                    self.__log_media(tmpchat_type, msg['pinned_message'])
            elif content_type == 'delete_chat_photo':
                dlog += " The photo of this "+chat_type + ' ' + \
                    msg['chat']['title'] + \
                    ' ( '+str(chat_id) + ' ) was deleted by '+fnick
                if fuserid:
                    dlog += " ( "+fuserid+" )"
            elif content_type == 'new_chat_title':
                dlog += " The title of this "+chat_type + " was changed to " +\
                    msg['new_chat_title'] + " by "
                if fuserid:
                    dlog += " ( "+fuserid+" )"
            else:
                dlog += ' ' + fnick
                if fuserid:
                    dlog += " ( "+fuserid+" )"
                dlog += " in channel" + \
                    msg['chat']['title'] + \
                    ' ( '+str(chat_id) + ' ) sent a ' + content_type
        self.clog(dlog)
        self.__log_media(content_type, msg)
        if flog != "":
            self.clog(flog)
        return

    def __log_media(self, content_type, msg):
        flog = ""
        if content_type == 'photo':
            flog = "[Photo]"
            photo_array = msg['photo']
            photo_array.reverse()
            try:
                flog = flog + "Caption = " + \
                    msg['caption'] + " ,FileID:" + photo_array[0]['file_id']
            except:
                flog = flog + "FileID:" + photo_array[0]['file_id']
        elif content_type == 'audio':
            flog = "[Audio]"
            try:
                flog = flog + "Caption = " + \
                    msg['caption'] + " ,FileID:" + msg['audio']['file_id']
            except:
                flog = flog + "FileID:" + msg['audio']['file_id']
        elif content_type == 'document':
            flog = "[Document]"
            try:
                flog = flog + "Caption = " + \
                    msg['caption'] + " ,FileID:" + msg['document']['file_id']
            except:
                flog = flog + "FileID:" + msg['document']['file_id']
        elif content_type == 'video':
            flog = "[Video]"
            try:
                flog = flog + "Caption = " + \
                    msg['caption'] + " ,FileID:" + msg['video']['file_id']
            except:
                flog = flog + "FileID:" + msg['video']['file_id']
        elif content_type == 'voice':
            flog = "[Voice]"
            try:
                flog = flog + "Caption = " + \
                    msg['caption'] + " ,FileID:" + msg['voice']['file_id']
            except:
                flog = flog + "FileID:" + msg['voice']['file_id']
        elif content_type == 'sticker':
            flog = "[Sticker]"
            try:
                flog = flog + "Caption = " + \
                    msg['caption'] + " ,FileID:" + msg['sticker']['file_id']
            except:
                flog = flog + "FileID:" + msg['sticker']['file_id']
        if flog != "":
            self.clog(flog)
        return

    def clog(self, text):
        print(text)
        self.log(text)

    def log(self, text):
        if text[0:7] == "[Debug]":
            if config.Debug == True:
                with io.open(self.logpath+"-debug.log", "a", encoding='utf8') as logger:
                    logger.write(
                        "["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "")+"]"+text+"\n")
            return
        with io.open(self.logpath+".log", "a", encoding='utf8') as logger:
            logger.write(text+"\n")
        return

logger = Log()
try:
    if sys.argv[1] == 'test':
        print('There is no santax error,exiting...')
        exit()
    else:
        raise SyntaxError("Invaild command santax: {0}".format(sys.argv[1]))
except IndexError:
    pass

botwoasync = telepot.Bot(config.TOKEN)
bot = telepot.aio.Bot(config.TOKEN)
data = Datas()

class botprofile:
    def __init__(self):
        self.__bot_me = botwoasync.getMe()
        self.id = self.__bot_me['id']
        self.first_name = self.__bot_me['first_name']
        self.username = self.__bot_me['username']
bot_me = botprofile()

answerer = telepot.helper.Answerer(bot)
loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot, {'chat': on_chat_message,
                                   'callback_query': on_callback_query}).run_forever())
logger.clog("["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'",
                                                           "")+"][Info] Bot has started")
logger.clog(
    "["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "")+"][Info] Listening ...")
try:
    loop.run_forever()
except KeyboardInterrupt:
    logger.clog("["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'","")+"][Info] Interrupt signal received,stopping.")
