import { Telegram } from 'telegraf';
import { TelegramCore } from '../../Components/Telegram/Core';
import { Chat, ChatMemberAdministrator } from 'typegram';
import { Logger } from 'tslog-helper';
import { Core } from '../..';
import { Config } from '../Config';
import { EventEmitter } from 'events';

export class PillPosting extends EventEmitter{
    private logger: Logger;
    private config: Config;
    private telegram: Telegram;

    private channels: { id: number, name: string, admins: number[], groups: number[], username: string | undefined }[] = [];
    
    /**
     * PillPosting Core
     */
    constructor(core: Core, telegram: TelegramCore) {
        super();

        this.logger = core.mainLogger.getChildLogger({ name: 'PillPosting' });
        this.config = core.config;
        this.telegram = telegram.client.telegram;
        this.loadChannels().then(() => this.emit('ready'));
    }

    /**
    * Load Channels from Config
    */
    private async loadChannels() {
        this.logger.info('Loading channels to cache...');

        for (const channelConfig of this.config.pillPosting.channels) {
            await this.loadChannelChat(channelConfig.username || channelConfig.id);
        }

        this.config.save();
        this.logger.info(`Loaded ${this.channels.length} channel${(this.channels.length > 1) ? 's' : ''}`);
    }

    /**
    * Load Channel from id or username
    * @param idOrUsername Channel id or idOrUsername
    * @param groups [Optional] Channel post group from config
    */
    private async loadChannelChat(idOrUsername: number | string, groups: number[] | undefined = undefined) {
        try {
            const fetchInfo = (await this.telegram.getChat(idOrUsername)) as Chat.ChannelGetChat;
            if (typeof idOrUsername === 'string') this.config.upgradeChannel(idOrUsername, fetchInfo.id);
            await this.loadChannel(fetchInfo, groups);
        } catch (error) {
            this.logger.error(`Chat ${idOrUsername} fetch failed:`, error);
        }
    }

    /**
    * Add or update Channel from chat
    * @param chat Channel chat object
    * @param groups [Optional] Channel post group from config
    */
    private async loadChannel(chat: Chat.ChannelGetChat, groups: number[] | undefined = undefined) {
        let index = this.channels.findIndex(value => value.id === chat.id);

        if (index === -1) {
            this.channels.push({ id: chat.id, name: '', admins: [], groups: [], username: undefined });
            index = this.channels.findIndex(value => value.id === chat.id);
        }

        this.channels[index].name = chat.title;
        this.channels[index].username = chat.username;

        try {
            const chatAdmins = (await this.telegram.getChatAdministrators(this.channels[index].id)).map((value) => value as ChatMemberAdministrator);
            for (const admin of chatAdmins) {
                if (admin.can_post_messages) {
                    this.channels[index].admins.push(admin.user.id);
                }
            }
        } catch (error) {
            this.logger.error(`Admin list of ${this.channels[index].id} fetch failed:`, error);
        }

        if (groups) this.channels[index].groups = groups;
        
        this.logger.debug('Channel info updated:', this.channels[index]);
    }
}