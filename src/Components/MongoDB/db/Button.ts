import { ObjectId, Collection } from 'mongodb';
import { Logger } from 'tslog-helper';
import { Core } from '../../..';
import { Cache } from '../../../Core/Cache';
import { ERR_CLIENT_NOT_INIT, ERR_DB_NOT_INIT, ERR_INSERT_FAILURE } from '../Core';

export interface IButton {
    _id: ObjectId;
    type: string; // todo restrict string
    action: IAction;
}

export interface IAction { // todo
    value: string;
}

export class DbButton {
    private database?: Collection<IButton>;
    private logger: Logger;
    private _cache: Cache<IButton>;

    constructor(core: Core) {
        this.logger = core.mongodb.logger.getChildLogger({ name : 'DbButton'});
        if (!core.mongodb.client) throw ERR_CLIENT_NOT_INIT;
        this.database = core.mongodb.client.collection('Buttons');
        
        // init cached
        this._cache = new Cache<IButton>(core, 'Users');
    }

    public async create(button: IButton): Promise<IButton> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const insert = await this.database.insertOne(button);
        if (!insert.acknowledged) throw ERR_INSERT_FAILURE;
        button._id = insert.insertedId;
        this._cache.createOrUpdate(button._id.toString(), button);
        this.logger.debug('New button created:', button);
        return button;
    }

    public async get(id: ObjectId): Promise<IButton | null> {
        if (!this.database) throw ERR_DB_NOT_INIT;

        const data = this._cache.get(id.toString()) || await this.database.findOne({ _id:id });

        return data;
    }
    
    public async delete(id: ObjectId) {
        if (!this.database) throw ERR_DB_NOT_INIT;

        this._cache.delete(id.toString());
        await this.database.findOneAndDelete({ _id:id });
    }
}
