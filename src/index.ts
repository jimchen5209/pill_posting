import { LogHelper } from 'tslog-helper';
import { Config } from './Core/Config';
import { MongoDB } from './Core/MongoDB';
export class Core {
    private logHelper = new LogHelper();
    public readonly mainLogger = this.logHelper.logger;
    public readonly config = new Config(this);
    public readonly mongodb = new MongoDB(this);
    
    constructor() {
        this.logHelper.setDebug(this.config.debug);
        // eslint-disable-next-line no-unused-expressions,@typescript-eslint/no-unused-expressions
        // new Telegram();
    }
}

// eslint-disable-next-line no-unused-expressions,@typescript-eslint/no-unused-expressions
new Core();