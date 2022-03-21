import { ObjectId } from 'mongodb';
// import { IPost } from './Post';

export interface IProfile {
    _id: ObjectId;
    lang: string;
    postsRaw: ObjectId[];
    // posts: IPost[] | undefined;
}
