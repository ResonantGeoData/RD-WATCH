import { reactive } from "vue";

import type { Region } from "./client";

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
  settings: {
    autoZoom: boolean;
  };
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
  filters: MapFilters;
  patterns: {
    patternThickness: number;
    patternOpacity: number;
  };
  regionMap: Record<Region["id"], Region["name"]>
}>({
  timestamp: Math.floor(Date.now() / 1000),
  settings: {
    autoZoom: false,
  },
  bbox: {
    xmin: -180,
    ymin: -90,
    xmax: 180,
    ymax: 90,
  },
  filters: {
    groundTruthPattern: false,
    otherPattern: false,
  },
  patterns: {
    patternThickness: 8,
    patternOpacity: 255,
  },
  regionMap: {}
});
