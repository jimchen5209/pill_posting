import { Telegraf } from 'telegraf';
import { UserFromGetMe } from 'typegram';
import { Logger } from 'tslog-helper';
import { Core } from '../..';
import { Config } from '../../Core/Config';
import { PillPosting } from '../../Core/PillPosting/Core';

export class TelegramCore {
    private _client: Telegraf;
    private _self: UserFromGetMe | undefined;
    private logger: Logger;
    private config: Config;
    private pillPosting: PillPosting;

    /**
     * Telegram Core
     */
    constructor(core: Core) {
        this.config = core.config;
        this.logger = core.mainLogger.getChildLogger({ name: 'Telegram'});
        this.logger.info('Starting Telegram...');
        this._client = new Telegraf(this.config.telegram.botToken, { telegram: { apiRoot: this.config.telegram.baseApi?.url } });
        this._client.telegram.getMe().then((me: UserFromGetMe) => {
            this._self = me;
            this.logger.info(`Logined as ${this._self.first_name}@${this._self.username}(${this._self.id})`);
        });
        this.pillPosting = new PillPosting(core, this);
        this.pillPosting.once('ready', () => {
            this._client.launch();
            this.logger.info('Bot has started. Listening...');
        });
    }

    /**
     * Telegram Client
     */
    public get client(): Telegraf {
        return this._client;
    }

    /**
     * Graceful Stop telegram client
     */
    public stop(signal: string) {
        this._client.stop(signal);
    }
}