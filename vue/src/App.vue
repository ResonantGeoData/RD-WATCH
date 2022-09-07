<script setup lang="ts">
import { map } from "./map";
import EvaluationList from "./components/EvaluationList.vue";

map.addSource("all-sites", {
  type: "vector",
  tiles: [
    `${location.protocol}//${location.host}/api/site/tile/{z}/{x}/{y}.pbf`,
  ],
  maxzoom: 14,
});

map.addLayer({
  id: "site-background",
  type: "fill",
  source: "all-sites",
  "source-layer": "default",
  paint: {
    "fill-color": "#088",
  },
});

map.addLayer({
  id: "site-hover",
  type: "fill",
  source: "all-sites",
  "source-layer": "default",
  paint: {
    "fill-color": "#FFA500",
    "fill-opacity": [
      "case",
      ["boolean", ["feature-state", "hover"], false],
      1,
      0,
    ],
  },
});

map.addLayer({
  id: "site-focus",
  type: "line",
  source: "all-sites",
  "source-layer": "default",
  paint: {
    "line-color": "RGBA(255, 165, 0, 1)",
    "line-width": 2,
    "line-opacity": [
      "case",
      ["boolean", ["feature-state", "focus"], false],
      1,
      0,
    ],
  },
});
</script>

<template>
  <div class="" relative>
    <div class="fixed h-screen w-80 pt-2 pb-2 pl-2">
      <div
        class="relative h-full overflow-hidden rounded-xl bg-white drop-shadow-2xl"
      >
        <div class="relative h-20 rounded-t-xl bg-gray-100 pt-4 pl-4 pr-4">
          <img
            class="mx-auto pb-4"
            src="./assets/logo.svg"
            alt="Resonant GeoData"
          />
        </div>
        <div class="relative h-[calc(100%_-_5rem)] rounded-b-xl">
          <EvaluationList />
        </div>
      </div>
    </div>
  </div>
</template>
