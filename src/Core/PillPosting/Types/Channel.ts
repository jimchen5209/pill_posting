export interface IChannel {
    id: number;
    name: string;
    admins: number[];
    groups: number[];
    username: string | undefined;
}
