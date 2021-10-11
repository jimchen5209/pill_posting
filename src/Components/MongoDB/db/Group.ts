import { Collection, ObjectId, ReturnDocument } from 'mongodb';
import { Logger } from 'tslog-helper';
import { Core } from '../../..';
import { Cache } from '../../../Core/Cache';
import { ERR_CLIENT_NOT_INIT, ERR_DB_NOT_INIT, ERR_INSERT_FAILURE } from '../Core';
import { IProfile } from './IProfile';
import { IPost } from './Post';

export interface IGroup extends IProfile {
    chatId: number;
}

export class DbGroup {
    private database?: Collection<IGroup>;
    private logger: Logger;
    private _cache: Cache<IGroup>;

    constructor(core: Core) {
        this.logger = core.mongodb.logger.getChildLogger({ name: 'DbGroup' });
        if (!core.mongodb.client) throw ERR_CLIENT_NOT_INIT;
        this.database = core.mongodb.client.collection('Groups');
        this.database.createIndex({ chatId: 1 });

        // init cached
        this._cache = new Cache<IGroup>(core, 'Groups');
    }

    public async create(chatId: number, lang: string): Promise<IGroup> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const postsRaw: ObjectId[] = [];
        const data = { chatId, lang, postsRaw } as IGroup;

        const insert = await this.database.insertOne(data);
        if (!insert.acknowledged) throw ERR_INSERT_FAILURE;
        data._id = insert.insertedId;
        this._cache.createOrUpdate(chatId.toString(), data);
        this.logger.debug('New group profile created:', data);
        return data;
    }

    public async get(chatId: number, reloadPost = false): Promise<IGroup | null> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const data = this._cache.get(chatId.toString()) || await this.database.findOne({ chatId });

        if (data && reloadPost) {
            const newData = await this.loadPost(data);
            this._cache.createOrUpdate(chatId.toString(), newData);
            return newData;
        }

        return data;

    }

    public async updateLang(chatId: number, lang: string): Promise<IGroup | null> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const changedData = (await this.database.findOneAndUpdate(
            { chatId },
            { $set: { lang } },
            { returnDocument: ReturnDocument.AFTER }
        )).value;

        if (changedData) {
            this.logger.debug('Group data updated:', changedData);
            this._cache.createOrUpdate(chatId.toString(), changedData);
        }

        return changedData;
    }

    public pushPost(chatId: number, post: IPost): Promise<IGroup | null> {
        return this.pushPostById(chatId, post._id, true);
    }

    public async pushPostById(chatId: number, post: ObjectId, reloadPost = false): Promise<IGroup | null> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const changedData = (await this.database.findOneAndUpdate(
            { chatId },
            { $push: { postsRaw: post } },
            { returnDocument: ReturnDocument.AFTER }
        )).value;

        if (changedData) {
            this.logger.debug('Group data updated:', changedData);
            this._cache.createOrUpdate(chatId.toString(), changedData);

            if (reloadPost) {
                const loadedData = await this.loadPost(changedData);
                this._cache.createOrUpdate(chatId.toString(), loadedData);
                return loadedData;
            }
        }

        return changedData;
    }

    public async loadPost(data: IGroup): Promise<IGroup> {
        // TODO
        return data;
    }
}
