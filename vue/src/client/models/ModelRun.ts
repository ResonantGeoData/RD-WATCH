import type { Performer } from "./Performer";
import type { Region } from "./Region";

export type ModelRun = {
  id: number;
  region: Region;
  title: string;
  performer: Performer;
  parameters: object;
  numsites: number;
  score: number | null;
  timestamp: number | null;
  timerange: {
    min: number;
    max: number;
  } | null;
  bbox: GeoJSON.Polygon | null;
};
