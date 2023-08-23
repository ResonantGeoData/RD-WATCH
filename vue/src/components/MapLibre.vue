<script setup lang="ts">
import { Map } from "maplibre-gl";
import { style } from "../mapstyle";
import {
  buildObservationFilter,
  buildSiteFilter,
} from "../mapstyle/rdwatchtiles";
import { filteredSatelliteTimeList, state } from "../store";
import { markRaw, onMounted, onUnmounted, reactive, shallowRef, watch, withDefaults } from "vue";
import type { FilterSpecification } from "maplibre-gl";
import type { ShallowRef } from "vue";
import { popupLogic, setPopupEvents } from "../interactions/mouseEvents";
import { satelliteLoading } from "../interactions/satelliteLoading";
import { setReference } from "../interactions/fillPatterns";
import { setSatelliteTimeStamp } from "../mapstyle/satellite-image";
import { isEqual, throttle } from 'lodash';
import { nextTick } from "vue";
import { updateImageMapSources } from "../mapstyle/images";

interface Props {
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  compact: false,
});

const mapContainer: ShallowRef<null | HTMLElement> = shallowRef(null);
const map: ShallowRef<null | Map> = shallowRef(null);

const modelRunVectorLayers = reactive<Set<number>>(new Set());

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
    // Add opened model runs to list of vector tile layers
    state.modelRuns.filter((m) => state.openedModelRuns.has(m.key)).map((m) => m.id).forEach((m) => { modelRunVectorLayers.add(m) })

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
          Array.from(modelRunVectorLayers),
        ),
        bounds: [
          [state.bbox.xmin, state.bbox.ymin],
          [state.bbox.xmax, state.bbox.ymax],
        ],
      })
    );
    map.value.keyboard.disable();
    popupLogic(map);
    setPopupEvents(map);
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
() => state.modelRuns, () => state.openedModelRuns], (newVals, oldVals) => {

  if (state.satellite.satelliteImagesOn) {
    throttledSetSatelliteTimeStamp(state, filteredSatelliteTimeList.value);
  }

  const newFilters = newVals[1];
  const oldFilters = oldVals[1];

  // Clear layers on region change
  if (!isEqual(newFilters.region_id, oldFilters.region_id)) {
    modelRunVectorLayers.clear();
  }

  const openedModelRunIds = state.modelRuns.filter((m) => state.openedModelRuns.has(m.key)).map((m) => m.id);

  // Add opened model runs to list of vector tile layers
  openedModelRunIds.forEach((m) => { modelRunVectorLayers.add(m) })

  if (map.value) {
    updateImageMapSources(state.timestamp, state.enabledSiteObservations, state.siteObsSatSettings, map.value )
  }
  map.value?.setStyle(
    style(state.timestamp, state.filters, state.satellite, state.enabledSiteObservations, state.siteObsSatSettings, Array.from(modelRunVectorLayers)),
  );

  const siteFilter = buildSiteFilter(state.timestamp, state.filters);
  const observationFilter = buildObservationFilter(
    state.timestamp,
    state.filters
  );
  openedModelRunIds.forEach(id => {
    setFilter(`sites-outline-${id}`, siteFilter);
    setFilter(`observations-fill-${id}`, observationFilter);
    setFilter(`observations-outline-${id}`, observationFilter);
    setFilter(`observations-text-${id}`, observationFilter);
  })

  setPopupEvents(map);
});

watch(
  () => state.bbox,
  (val) => fitBounds(val)
);

watch(() => props.compact, () => {
  // Wait for it to resize the map based on CSS before resizing and fitting
  nextTick(() => {
    map.value?.resize();
    if (props.compact) {
      fitBounds(state.bbox);
    }
  });
});

</script>

<template>
  <div
    ref="mapContainer"
    :class="{map: !compact, compactMap: compact}"
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

.compactMap {
  position: fixed;
  width: 100%;
  max-height:50vh;
  height: 50vh;
  z-index: -1;
  inset: 0;
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
