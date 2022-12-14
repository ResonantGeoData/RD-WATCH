import type { ModelRun } from "./ModelRun";

export type ModelRunList = {
  count: number;
  next: null | string;
  previous: null | string;
  timerange: {
    min: number;
    max: number;
  };
  bbox: GeoJSON.Polygon;
  results: ModelRun[];
};
