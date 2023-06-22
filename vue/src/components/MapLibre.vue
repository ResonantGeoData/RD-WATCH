<script setup lang="ts">
import { Map } from "maplibre-gl";
import { style } from "../mapstyle";
import {
  buildObservationFilter,
  buildSiteFilter,
} from "../mapstyle/rdwatchtiles";
import { filteredSatelliteTimeList, state } from "../store";
import { markRaw, onMounted, onUnmounted, shallowRef, watch } from "vue";
import type { FilterSpecification } from "maplibre-gl";
import type { ShallowRef } from "vue";
import { popupLogic } from "../interactions/mouseEvents";
import { satelliteLoading } from "../interactions/satelliteLoading";
import { setReference } from "../interactions/fillPatterns";
import { setSatelliteTimeStamp } from "../mapstyle/satellite-image";
import { throttle } from 'lodash';

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
        style: style(state.timestamp, {
          groundTruthPattern: false,
          otherPattern: false,
        },
          state.satellite,
          state.enabledSiteObservations,
          state.siteObsSatSettings,
          state.modelRuns.filter((m) => state.openedModelRuns.has(m.key))
        ),
        bounds: [
          [state.bbox.xmin, state.bbox.ymin],
          [state.bbox.xmax, state.bbox.ymax],
        ],
      })
    );
    map.value.keyboard.disable();
    popupLogic(map);
    satelliteLoading(map);
    setReference(map);
  }
});

onUnmounted(() => {
  map.value?.remove();
});
const throttledSetSatelliteTimeStamp = throttle(setSatelliteTimeStamp, 300);


watch([() => state.timestamp, () => state.filters, () => state.satellite, () => state.filters.scoringColoring,
  () => state.satellite.satelliteSources, () => state.enabledSiteObservations, () => state.filters.hoverSiteId,
  () => state.modelRuns, () => state.openedModelRuns], () => {

  if (state.satellite.satelliteImagesOn) {
    throttledSetSatelliteTimeStamp(state, filteredSatelliteTimeList.value);
  }

  const openedModelRuns = state.modelRuns.filter((m) => state.openedModelRuns.has(m.key));

  map.value?.setStyle(
    style(state.timestamp, state.filters, state.satellite, state.enabledSiteObservations, state.siteObsSatSettings, openedModelRuns),
  );

  const siteFilter = buildSiteFilter(state.timestamp, state.filters);
  const observationFilter = buildObservationFilter(
    state.timestamp,
    state.filters
  );

  openedModelRuns.forEach(modelRun => {
    setFilter(`sites-outline-${modelRun.id}`, siteFilter);
    setFilter(`observations-fill-${modelRun.id}`, observationFilter);
    setFilter(`observations-outline-${modelRun.id}`, observationFilter);
    setFilter(`observations-text-${modelRun.id}`, observationFilter);
  })


});

watch(
  () => state.bbox,
  (val) => fitBounds(val)
);
</script>

<template>
  <div
    ref="mapContainer"
    class="map"
  />
</template>

<style>
@import "maplibre-gl/dist/maplibre-gl.css";

.map {
  position: fixed;
  width: 100vw;
  height: 100vh;
  inset: 0;
  z-index: -1;
}

.mapboxgl-popup {
  max-width: 400px;
  font-size: 1.5em;
  opacity: 1;
}

.mapboxgl-popup ul {
  opacity: 1;
}
</style>
