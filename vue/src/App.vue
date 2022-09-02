<script setup lang="ts">
import { map } from "./map";
import { LngLatBounds } from "maplibre-gl";
import EvaluationList from "./components/EvaluationList.vue";

setTimeout(() => {
  map.addSource("all-sites", {
    type: "vector",
    tiles: ["http://localhost:9000/api/site/tile/{z}/{x}/{y}.pbf"],
    maxzoom: 14,
    // bounds: [128.864341, 37.756224, 128.87397899999996, 37.763705],
  });
  map.addSource("all-observations", {
    type: "vector",
    tiles: ["http://localhost:9000/api/site/1/tile/{z}/{x}/{y}.pbf"],
    maxzoom: 14,
    // bounds: [128.864341, 37.756224, 128.87397899999996, 37.763705],
  });
  map.addLayer({
    id: "all-sites",
    type: "fill",
    source: "all-sites",
    "source-layer": "default",
    layout: {},
    paint: {
      "fill-color": "#088",
      "fill-opacity": 0.5,
    },
  });
  map.addLayer({
    id: "all-observations",
    type: "fill",
    source: "all-observations",
    "source-layer": "default",
    layout: {},
    paint: {
      "fill-color": "#FF007F",
      "fill-opacity": 0.5,
    },
  });
  map.fitBounds(
    LngLatBounds.convert([128.864341, 37.756224, 128.87397899999996, 37.763705])
  );
}, 2000);
</script>

<template>
  <div class="fixed h-screen w-80 pl-2 pt-2 pb-2">
    <div class="h-full rounded-xl bg-white p-4 drop-shadow-2xl">
      <img
        class="h-30 w-30 mx-auto pb-4"
        src="./assets/logo.svg"
        alt="Planet Earth"
      />
      <h1 class="pb-2 text-3xl font-semibold">Evaluations</h1>
      <div class="pt-4">
        <div>
          <input id="time" type="range" name="time" min="1" max="339" />
        </div>
        <EvaluationList />
      </div>
    </div>
  </div>
</template>
