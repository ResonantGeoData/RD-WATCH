import { reactive } from "vue";

export const state = reactive<{
  timestamp: number;
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
  filters: Record<string, string>;
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
