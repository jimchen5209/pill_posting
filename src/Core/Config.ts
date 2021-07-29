import { existsSync, readFileSync, writeFileSync } from 'fs';
import { Category } from 'logging-ts';
import { Core } from '..';

export class Config {
    public telegram: { botToken: string, admins: number[], baseApiUrl: string | undefined };
    public mongodb: { host: string, name: string };
    public debug: boolean;
    private logger: Category;

    constructor(core: Core) {
        this.logger = new Category('Config', core.mainLogger);
        this.logger.info('Loading Config...');

        const telegramDefault = { botToken: '', admins: [], baseApiUrl: undefined };
        const mongodbDefault = { host: '', name: '' };

        if (existsSync('./config.json')) {
            const config = JSON.parse(readFileSync('config.json', { encoding: 'utf-8' }));

            // take and merge config
            this.telegram = {
                botToken: (config.telegram.botToken) ? config.telegram.botToken : telegramDefault.botToken,
                admins: (config.telegram.admins) ? config.telegram.admins : telegramDefault.admins,
                baseApiUrl: (config.telegram.baseApiUrl) ? config.telegram.baseApiUrl : telegramDefault.baseApiUrl
            };
            this.mongodb = {
                host: (config.mongodb.host) ? config.mongodb.host : mongodbDefault.host,
                name: (config.mongodb.name) ? config.mongodb.name : mongodbDefault.name
            };
            this.debug = (config.Debug) ? config.Debug : false;
            
            this.write();
        } else {
            this.logger.error('Can\'t load config.json: File not found.', null);
            this.logger.info('Generating empty config...');
            this.telegram = telegramDefault;
            this.mongodb = mongodbDefault;
            this.debug = false;
            this.write();
            this.logger.info('Fill your config and try again.');
            process.exit(-1);
        }
    }

    private write() {
        const json = JSON.stringify({
            telegram: this.telegram,
            mongodb: this.mongodb,
            Debug: this.debug
        }, null, 4);
        writeFileSync('./config.json', json, 'utf8');
    }
}
