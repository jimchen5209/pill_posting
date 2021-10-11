import { Collection, ObjectId, ReturnDocument } from 'mongodb';
import { Logger } from 'tslog-helper';
import { Core } from '../../..';
import { Cache } from '../../../Core/Cache';
import { ERR_CLIENT_NOT_INIT, ERR_DB_NOT_INIT, ERR_INSERT_FAILURE } from '../Core';
import { IProfile } from './IProfile';
import { IPost } from './Post';

export interface IUser extends IProfile{
    userId: number;
}

export class DbUser {
    private database?: Collection<IUser>;
    private logger: Logger;
    private _cache: Cache<IUser>;

    constructor(core: Core) {
        this.logger = core.mongodb.logger.getChildLogger({ name : 'DbUser'});
        if (!core.mongodb.client) throw ERR_CLIENT_NOT_INIT;
        this.database = core.mongodb.client.collection('Users');
        this.database.createIndex({ userId: 1 });
        
        // init cached
        this._cache = new Cache<IUser>(core, 'Users');
    }

    public async create(userId: number, lang: string): Promise<IUser> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const postsRaw: ObjectId[] = [];
        const data = { userId, lang, postsRaw } as IUser;

        const insert = await this.database.insertOne(data);
        if (!insert.acknowledged) throw ERR_INSERT_FAILURE;
        data._id = insert.insertedId;
        this._cache.createOrUpdate(userId.toString(), data);
        this.logger.debug('New user created:', data);
        return data;
    }

    public async get(userId: number, reloadPost = false): Promise<IUser | null> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const data = this._cache.get(userId.toString()) || await this.database.findOne({ userId });

        if (data && reloadPost) {
            const newData = await this.loadPost(data);
            this._cache.createOrUpdate(userId.toString(), newData);
            return newData;
        }

        return data;

    }

    public async updateLang(userId: number, lang: string): Promise<IUser | null> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const changedData = (await this.database.findOneAndUpdate(
            { userId },
            { $set: { lang } },
            { returnDocument: ReturnDocument.AFTER }
        )).value;

        if (changedData) {
            this.logger.debug('User data updated:', changedData);
            this._cache.createOrUpdate(userId.toString(), changedData);
        }

        return changedData;
    }

    public pushPost(userId: number, post: IPost): Promise<IUser | null> {
        return this.pushPostById(userId, post._id, true);
    }

    public async pushPostById(userId: number, post: ObjectId, reloadPost = false): Promise<IUser | null> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const changedData = (await this.database.findOneAndUpdate(
            { userId },
            { $push: { postsRaw: post } },
            { returnDocument: ReturnDocument.AFTER }
        )).value;

        if (changedData) {
            this.logger.debug('User data updated:', changedData);
            this._cache.createOrUpdate(userId.toString(), changedData);

            if (reloadPost) {
                const loadedData = await this.loadPost(changedData);
                this._cache.createOrUpdate(userId.toString(), loadedData);
                return loadedData;
            }
        }

        return changedData;
    }

    public async loadPost(data: IUser): Promise<IUser> {
        // TODO
        return data;
    }
}
