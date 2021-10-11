import { scheduleJob } from 'node-schedule';
import { Logger } from 'tslog-helper';
import { Core } from '..';

export interface ICache<T> {
    data: T;
    ttl: number;
}

export class Cache<T> {
    private data: { [key: string]: ICache<T> } = {};
    private readonly ttlDefault = 7;
    private logger: Logger;

    /**
     * Cache manager for db content
     */
    constructor(core: Core, name: string) {
        this.logger = core.mainLogger.getChildLogger({ name: `Cache/${name}` });
        scheduleJob('0 0 * * *', () => {
            this.logger.debug('Changing ttl for cache');

            for (const key of Object.keys(this.data)) {
                if (!this.data[key]) continue;
                this.logger.debug(`${key}'s ttl is now ${--this.data[key].ttl}'`);

                if (this.data[key].ttl <= 0) {
                    this.logger.debug(`${key} has expired`);
                    this.delete(key);
                }
            }
        });
    }

    /**
     * 
     */
    public createOrUpdate(key: string, value: T): void {
        if (this.data[key]) {
            // Don't create object
            this.data[key].data = value;
            this.data[key].ttl = this.ttlDefault;
            this.logger.debug(`${key} updated`);
        } else {
            this.data[key] = { data: value, ttl: this.ttlDefault };
            this.logger.debug(`${key} created`);
        }
    }

    /**
     * 
     */
    public get(key: string): T | undefined {
        if (this.data[key]) {
            if (this.data[key].ttl > 0) return this.data[key].data;
            this.logger.debug(`${key} has expired`);
            this.delete(key);
        }
        return undefined;
    }

    /**
     * 
     */
    public delete(key: string): void {
        if (this.data[key]) delete this.data[key];
        this.logger.debug(`${key} deleted`);
    }

    /**
     * 
     */
    public clear(): void {
        for (const key of Object.keys(this.data)) {
            if (!this.data[key]) continue;

            this.delete(key);
        }
        this.logger.debug('Cache data cleared');
    }
}
