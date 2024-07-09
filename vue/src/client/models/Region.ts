export type Region = string;

export interface RegionDetail {
    name: string;
    ownerUsername: string;
    value: string;
    public: boolean;
    id: number;
    deleteBlock?: string;
    hasGeom?: boolean;
}