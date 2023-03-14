<script setup lang="ts">
import { Map } from "maplibre-gl";
import { style } from "../mapstyle";
import {
  buildObservationFilter,
  buildSiteFilter,
} from "../mapstyle/rdwatchtiles";
import { state } from "../store";
import { markRaw, onMounted, onUnmounted, shallowRef, watch } from "vue";
import type { FilterSpecification } from "maplibre-gl";
import type { ShallowRef } from "vue";
import { popupLogic } from "../interactions/popup";
import { buildSourceFilter } from "../mapstyle/satellite-image";
import { setReference } from "../interactions/fillPatterns";

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
        }, state.satellite
        ),
        bounds: [
          [state.bbox.xmin, state.bbox.ymin],
          [state.bbox.xmax, state.bbox.ymax],
        ],
      })
    );
    popupLogic(map);
    setReference(map);
  }
});

onUnmounted(() => {
  map.value?.remove();
});

watch([() => state.timestamp, () => state.filters, () => state.satellite], () => {
  if (state.satellite.satelliteImagesOn) {
    if (state.filters && state.satellite.satelliteTimeList && state.satellite.satelliteTimeList.length > 0) {
        const list = state.satellite.satelliteTimeList.map((item) => new Date(item));
        const base = new Date(state.timestamp * 1000);
        list.sort((a,b) => {
            const distanceA = Math.abs(base.valueOf() - a.valueOf());
            const distanceB = Math.abs(base.valueOf() - b.valueOf());
            return distanceA - distanceB;
        })
        const date = list[0];
        //const timeStamp = new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().substring(0,19);
        const timeStamp = date.toISOString().substring(0,19);
        state.satellite.satelliteTimeStamp = timeStamp;
        // if (state.satellite.satelliteTimeList.includes(timeStamp)) {
        //   state.satellite.satelliteTimeStamp = timeStamp;
        // } else 
        // {
        //   state.satellite.satelliteTimeStamp = null;
        // }
    }
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
    style(state.timestamp, state.filters, state.satellite)
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
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
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
