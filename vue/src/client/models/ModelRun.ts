import type { Performer } from "./Performer";
import type { Region } from "./Region";

export type ModelRun = {
  id: string;
  region: Region | null;
  title: string;
  performer: Performer;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  parameters: Record<string, any>;
  numsites: number;
  downloading: number;
  score: number | null;
  timestamp: number | null;
  timerange: {
    min: number;
    max: number;
  } | null;
  bbox: GeoJSON.Polygon | null;
  created: string;
  expiration_time: string;
  proposal?: null | 'PROPOSAL' | 'APPROVED';
  groundTruthLink?: string;
  adjudicated?: {
    proposed: number,
    other: number,
    ground_truths?: string,
  } | null;
  mode: 'batch' | 'incremental' | null;
};
