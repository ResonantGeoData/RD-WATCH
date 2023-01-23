<script setup lang="ts">
import { Map, Popup } from "maplibre-gl";
import { style } from "../mapstyle";
import {
  buildObservationFilter,
  buildSiteFilter,
} from "../mapstyle/rdwatchtiles";
import { state } from "../store";
import { markRaw, onMounted, onUnmounted, shallowRef, watch } from "vue";
import type { FilterSpecification } from "maplibre-gl";
import type { ShallowRef } from "vue";

const mapContainer: ShallowRef<null | HTMLElement> = shallowRef(null);
const map: ShallowRef<null | Map> = shallowRef(null);

function setFilter(layerID: string, filter: FilterSpecification) {
  map.value?.setFilter(layerID, filter, {
    validate: false,
  });
}

function fitBounds(bbox: typeof state["bbox"]) {
  map.value?.fitBounds(
    [
      [bbox.xmin, bbox.ymin],
      [bbox.xmax, bbox.ymax],
    ],
    {
      padding: 160,
      offset: [80, 0],
    }
  );
}

onMounted(() => {
  if (mapContainer.value !== null) {
    map.value = markRaw(
      new Map({
        container: mapContainer.value,
        style: style(state.timestamp, {}),
        bounds: [
          [state.bbox.xmin, state.bbox.ymin],
          [state.bbox.xmax, state.bbox.ymax],
        ],
      })
    );
    map.value.on('load', () => {
      const size = 8;
      const bytesPerPixel = 4
      const dataRight = new Uint8Array(size * size * bytesPerPixel);
      const dataLeft = new Uint8Array(size * size * bytesPerPixel);
      // Generate our pattern from the pixels
      const X = [0, 0, 0, 255]; //RGBA
      const O = [0, 0, 0, 0];
      const patternRight = [ 
               O, O, O, O, O, O, X, X,
               O, O, O, O, O, X, X, X,
               O, O, O, O, X, X, X, O,
               O, O, O, X, X, X, O, O,
               O, O, X, X, X, O, O, O,
               O, X, X, X, O, O, O, O,
               X, X, X, O, O, O, O, O,
               X, X, O, O, O, O, O, O,
              ];
      const patternLeft = [ 
               X, X, O, O, O, O, O, O,
               X, X, X, O, O, O, O, O,
               O, X, X, X, O, O, O, O,
               O, O, X, X, X, O, O, O,
               O, O, O, X, X, X, O, O,
               O, O, O, O, X, X, X, O,
               O, O, O, O, O, X, X, X,
               O, O, O, O, O, O, X, X,
              ];
      for (let i = 0; i < patternRight.length; i += 1) {
        for (let bit = 0; bit < 4; bit += 1) {
          
          dataRight[(4*i) + bit] = patternRight[i][bit];
          dataLeft[(4*i) + bit] = patternLeft[i][bit];
        }
      }

      if (map.value) {
        map.value.addImage('diagonal-right', { width: size, height: size, data: dataRight });
        map.value.addImage('diagonal-left', { width: size, height: size, data: dataLeft });
      }
    });
  }
});

onUnmounted(() => {
  map.value?.remove();
});

watch([() => state.timestamp, () => state.filters], () => {
  const siteFilter = buildSiteFilter(state.timestamp, state.filters);
  const observationFilter = buildObservationFilter(
    state.timestamp,
    state.filters
  );
  setFilter("sites-outline", siteFilter);
  setFilter("observations-fill", observationFilter);
  setFilter("observations-outline", observationFilter);
  setFilter("observations-text", observationFilter);
});

watch(
  () => state.bbox,
  (val) => fitBounds(val)
);
</script>

<template>
  <div ref="mapContainer" class="map"></div>
</template>

<style>
@import "maplibre-gl/dist/maplibre-gl.css";

.map {
  position: fixed;
  width: 100vw;
  height: 100vh;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: -1;
}
</style>
