import { LogHelper } from 'tslog-helper';
import { Config } from './Core/Config';
import { MongoDB } from './Components/MongoDB/Core';
import { TelegramCore } from './Components/Telegram/Core';

export class Core {
    private readonly logHelper = new LogHelper();
    public readonly mainLogger = this.logHelper.logger;
    public readonly config = new Config(this);
    public readonly mongodb = new MongoDB(this);
    public readonly telegram: TelegramCore;
    
    /**
     *  Core
     */
    constructor() {
        this.logHelper.setDebug(this.config.logging.debug);
        this.logHelper.setLogRaw(this.config.logging.raw);
        this.telegram = new TelegramCore(this);

        // Enable graceful stop
        process.once('SIGINT', () => this.stop('SIGINT'));
        process.once('SIGTERM', () => this.stop('SIGTERM'));
    }

    /**
     * Graceful Stop
     */
    private stop(signal: string) {
        this.telegram.stop(signal);
        process.exit(0);
    }
}

// eslint-disable-next-line no-unused-expressions,@typescript-eslint/no-unused-expressions
new Core();