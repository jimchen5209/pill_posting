import { Collection, ObjectId } from 'mongodb';
import { Logger } from 'tslog-helper';
import { Core } from '../../..';
import { Cache } from '../../../Core/Cache';
import { IChannel } from '../../../Core/PillPosting/Types/Channel';
import { ERR_CLIENT_NOT_INIT, ERR_DB_NOT_INIT, ERR_INSERT_FAILURE } from '../Core';
import { IGroup } from './Group';
import { IUser } from './User';

export interface IPost {
    _id: ObjectId;
    ownerId: number;
    owner: IUser | undefined;
    groupId: number | undefined;
    group: IGroup | undefined;
    targetChannelsId: number[];
    targetChannels: IChannel[] | undefined;
    anonymous: boolean;
    removeForwardSenders: boolean;
    messages: IMessage[];
    postMessage: IMessage;
    manageMessages: IMessage[];
    status: 'pending' | 'accepted' | 'rejected' | 'cancelled';
}

export interface IMessage {
    chatId: number;
    messageId: number;
    media_group_id: string | undefined;
}
 
export class DbPost {
    private database?: Collection<IPost>;
    private logger: Logger;
    private _cache: Cache<IPost>;

    constructor(core: Core) {
        this.logger = core.mongodb.logger.getChildLogger({ name: 'DbPost' });
        if (!core.mongodb.client) throw ERR_CLIENT_NOT_INIT;
        this.database = core.mongodb.client.collection('Posts');
        this.database.createIndex({ ownerId: 1, groupId: 1 });

        // init cached
        this._cache = new Cache<IPost>(core, 'Posts');
    }

    public async create(ownerId: number, targetChannelsId: number[], anonymous: boolean, removeForwardSenders: boolean, messages: IMessage[], postMessage: IMessage, manageMessages: IMessage[], groupId: number|undefined = undefined): Promise<IPost> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const data = { ownerId, groupId, targetChannelsId, anonymous, removeForwardSenders, messages, postMessage, manageMessages, status: 'pending'} as IPost;

        const insert = await this.database.insertOne(data);
        if (!insert.acknowledged) throw ERR_INSERT_FAILURE;
        data._id = insert.insertedId;
        this._cache.createOrUpdate(data._id.toString(), data);
        this.logger.debug('New group profile created:', data);
        return data;
    }

    public async getById(id: ObjectId, reloadData = false): Promise<IPost | null> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const data = this._cache.get(id.toString()) || await this.database.findOne({ _id: id });

        if (data && reloadData) {
            const newData = await this.load(data);
            this._cache.createOrUpdate(id.toString(), newData);
            return newData;
        }

        return data;
    }

    public async getListByOwner(ownerId: number): Promise<IPost[]> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const data = await this.database.find({ ownerId }).toArray();

        return data;
    }

    public async getListByGroup(groupId: number): Promise<IPost[]> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        return await this.database.find({ groupId }).toArray();
    }

    public async getListByOwnerAndGroup(ownerId: number, groupId: number): Promise<IPost[]> {
        if (!this.database) throw ERR_DB_NOT_INIT;
        
        return await this.database.find({ ownerId, groupId }).toArray();
    }

    public async load(data: IPost): Promise<IPost> {
        // TODO
        return data;
    }
}
