import { catService } from 'logging-ts';
import { Config } from './Core/Config';
import { MongoDB } from './Core/MongoDB';
export class Core {
    public readonly mainLogger = catService;
    public readonly config = new Config(this);
    public readonly mongodb = new MongoDB(this);
    
    constructor() {
        // eslint-disable-next-line no-unused-expressions,@typescript-eslint/no-unused-expressions
        // new Telegram();
    }
}

// eslint-disable-next-line no-unused-expressions,@typescript-eslint/no-unused-expressions
new Core();