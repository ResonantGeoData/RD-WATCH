export type Region = string;

export interface RegionDetail {
    name: string;
    owner: string;
    value: string;
    public: boolean;
    id: number;
    deleteBlock?: false | string;
}