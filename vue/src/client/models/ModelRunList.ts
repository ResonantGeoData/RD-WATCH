import type { ModelRun } from "./ModelRun";

export type ModelRunList = {
  count: number;
  next: null | string;
  previous: null | string;
  timerange: {
    min: number;
    max: number;
  } | null;
  bbox: GeoJSON.Polygon | null;
  items: ModelRun[];
};

export const emptyModelRunList = (): ModelRunList => ({
  count: 0,
  next: null,
  previous: null,
  timerange: null,
  bbox: null,
  items: [],
});
