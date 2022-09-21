import { reactive } from "vue";

export const state = reactive({
  timestamp: Math.floor(Date.now() / 1000),
  bbox: {
    xmin: -180,
    ymin: -90,
    xmax: 180,
    ymax: 90,
  },
});
