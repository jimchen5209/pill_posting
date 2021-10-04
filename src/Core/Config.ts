import { existsSync, readFileSync, writeFileSync } from 'fs';
import { Logger } from 'tslog-helper';
import { Core } from '..';

export class Config {
    private configVersion = 3.1;
    private _pillPosting: { channels: { id: number, groups: number[], username: string | undefined }[], adminGroups: number[], queueLimit: number};
    private _telegram: { botToken: string, admins: number[], baseApi: { url: string, local: boolean } | undefined };
    private _mongodb: { host: string, name: string };
    private _logging: { debug: boolean, raw: boolean };
    private logger: Logger;

    /**
     * Config Manager Core
     */
    constructor(core: Core) {
        this.logger = core.mainLogger.getChildLogger({ name: 'Config' });
        this.logger.info('Loading Config...');

        const pillPostingDefault = { channels: [], adminGroups: [], queueLimit: 12 };
        const telegramDefault = { botToken: '', admins: [], baseApi: undefined };
        const telegramBaseApiDefault = { url: 'http://localhost:8081', local: true };
        const mongodbDefault = { host: 'mongodb://localhost:27017', name: 'PillPosting' };
        const loggingDefault = { debug: false, raw: false };

        let versionChanged = false;

        if (existsSync('./config.json')) {
            const config = JSON.parse(readFileSync('config.json', { encoding: 'utf-8' }));

            if (!config.configVersion || config.configVersion < this.configVersion) versionChanged = true;
            if (config.configVersion > this.configVersion) {
                this.logger.fatal('This config version is newer than me! Consider upgrading to the latest version or reset your configuration.', null);
                process.exit(1);
            }

            // take and merge config
            if (!config.pillPosting) config.pillPosting = {};
            this._pillPosting = {
                channels: config.pillPosting.channels || pillPostingDefault.channels,
                adminGroups: config.Admin_groups || config.pillPosting.adminGroups || pillPostingDefault.adminGroups,
                queueLimit: config.queue_limit || config.pillPosting.queueLimit || pillPostingDefault.queueLimit
            };
            if (config.Channels) {
                for (const channel of config.Channels) {
                    const channelMigrate: { id: number, groups: number[], username: string | undefined } = {
                        id: -1,
                        groups: [],
                        username: undefined
                    };
                    if ((typeof channel.channel) === 'string') {
                        channelMigrate.username = channel.channel;
                    } else {
                        channelMigrate.id = channel.channel;
                    }
                    channelMigrate.groups = channel.groups;
                    this._pillPosting.channels.push(channelMigrate);
                }
            }

            
            if (!config.telegram) config.telegram = {};
            this._telegram = {
                botToken: config.TOKEN || config.telegram.botToken || telegramDefault.botToken,
                admins: config.telegram.admins || telegramDefault.admins,
                baseApi: telegramDefault.baseApi
            };
            if (config.Admin) this._telegram.admins.push(config.Admin);
            if (config.telegram.baseApi) {
                this._telegram.baseApi = {
                    url: config.telegram.baseApi.url || telegramBaseApiDefault.url,
                    local: config.telegram.baseApi.local || telegramBaseApiDefault.local
                };
            }

            if (!config.mongodb) config.mongodb = {};
            if (config.MongoDB) config.mongodb.name = config.MongoDB.name;
            let connectString;
            if (config.MongoDB && config.MongoDB.ip && config.MongoDB.port) {
                connectString = `mongodb://${config.MongoDB.ip}:${config.MongoDB.port}`;
            }
            this._mongodb = {
                host: connectString || config.mongodb.host || mongodbDefault.host,
                name: config.mongodb.name || mongodbDefault.name
            };
            
            if (!config.logging) config.logging = {};
            this._logging = {
                debug: config.Debug || config.debug || config.logging.debug || loggingDefault.debug,
                raw: config.logging.debug || loggingDefault.raw
            };
            
            this.save();


            if (versionChanged) {
                this.logger.info('Detected config version change and we have tried to migrate into it! Consider checking your config file.');
                process.exit(1);
            }
        } else {
            this.logger.error('Can\'t load config.json: File not found.', null);
            this.logger.info('Generating empty config...');
            this._pillPosting = pillPostingDefault;
            this._telegram = telegramDefault;
            this._mongodb = mongodbDefault;
            this._logging = loggingDefault;
            this.save();
            this.logger.info('Fill your config and try again.');
            process.exit(-1);
        }
    }

    /**
     * Configs for pill posting core
     */
    public get pillPosting() {
        return this._pillPosting;
    }

    /**
     * Configs for telegram bot
     */
    public get telegram() {
        return this._telegram;
    }

    /**
     * Configs for mongoDB
     */
    public get mongodb() {
        return this._mongodb;
    }

    /**
     * Configs for logging
     */
    public get logging() {
        return this._logging;
    }

    /**
     * Upgrade username based config into id based
     * @param username Channel username to change
     * @param serverId Channel id to merge into
     */
    public upgradeChannel(username: string, serverId: number): boolean {
        this.logger.debug(`Attempting to update ${username} to ${serverId}`);
        const index = this._pillPosting.channels.findIndex(value => value.username === username);
        if (index === -1) return false;
        this._pillPosting.channels[index].id = serverId;
        delete this._pillPosting.channels[index].username;
        return true;
    }

    /**
     * Save cached config into file
     */
    public save() {
        const json = JSON.stringify({
            '//configVersion': 'DO NOT MODIFY THIS UNLESS YOU KNOW WHAT YOU ARE DOING!!!!!',
            configVersion: this.configVersion,
            '//pillPosting': 'Configs for pill posting core.',
            '//pillPosting.channels': 'List of { id: <channel id in number>, groups: <list of channel posting group id in number> }.',
            '//pillPosting.adminGroups': 'List of admin group id in number.',
            '//pillPosting.queueLimit': 'Number of message limit for a single post.',
            pillPosting: this._pillPosting,
            '//telegram': 'Configs for telegram bot.',
            '//telegram.botToken': 'Telegram bot token get from @BotFather.',
            '//telegram.admins': 'list of bot admins\' uid in number.',
            '//telegram.baseApi': 'Set up here if you have setup a local bot api server.',
            '//telegram.baseApi(Note1)': 'You\'ll need to create this entry manually.',
            '//telegram.baseApi(Note2)': 'You can simply leave {} in this entry to use localhost:8081 with local mode enabled.',
            '//telegram.baseApi(Note3)': 'Bot will use telegram\'s default server when this entry is not exist.',
            '//telegram.baseApi.url': 'Local bot api server url.',
            '//telegram.baseApi.local': 'Is your bot server runs in local mode (start with --local).',
            telegram: this._telegram,
            '//mongodb': 'Configs for mongoDB.',
            '//mongodb.host': 'Connection string.',
            '//mongodb.name': 'Database name.',
            mongodb: this._mongodb,
            '//logging': 'Configs for logging.',
            '//logging.debug': 'Prints and file silly, trace and debug logs.',
            '//logging.raw': 'File raw json logs.',
            logging: this._logging
        }, null, 4);
        this.logger.debug('Config to write:', json);
        try {
            writeFileSync('./config.json', json, 'utf8');
            this.logger.info('Config saved.');
        } catch (err) {
            this.logger.error('Error writing config', err);
        }
    }
}
