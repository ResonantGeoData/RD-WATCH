import { reactive } from "vue";

export interface MapFilters {
  configuration_id?: number[];
  performer_id?: number[];
  region_id?: number[];
  showSiteOutline?: boolean;
  groundTruthPattern?: boolean;
  otherPattern?: boolean;
}

export const state = reactive<{
  timestamp: number;
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
  filters: MapFilters;
  patterns?: {
    patternThickness?: number;
    patternOpacity?: number
  },
}>({
  timestamp: Math.floor(Date.now() / 1000),
  bbox: {
    xmin: -180,
    ymin: -90,
    xmax: 180,
    ymax: 90,
  },
  filters: {},
});
