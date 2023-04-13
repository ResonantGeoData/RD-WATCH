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
import { popupLogic } from "../interactions/popup";
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
        style: style(state.timestamp,  {
          groundTruthPattern: false,
          otherPattern: false,
        }, state.satellite,
        state.enabledSiteObservations,
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


watch([() => state.timestamp, () => state.filters, () => state.satellite,
() => state.satellite.satelliteSources, () => state.enabledSiteObservations], () => {
  if (state.satellite.satelliteImagesOn) {
    throttledSetSatelliteTimeStamp(state, filteredSatelliteTimeList.value);
  }
  const siteFilter = buildSiteFilter(state.timestamp, state.filters);
  const observationFilter = buildObservationFilter(
    state.timestamp,
    state.filters
  );
  setFilter("sites-outline", siteFilter);
  setFilter("observations-fill", observationFilter);
  setFilter("observations-outline", observationFilter);
  setFilter("observations-text", observationFilter);
  map.value?.setStyle(
    style(state.timestamp, state.filters, state.satellite, state.enabledSiteObservations)
  );

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
