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
import useEditPolygon from "../interactions/editGeoJSON";
import { satelliteLoading } from "../interactions/satelliteLoading";
import { setReference } from "../interactions/fillPatterns";
import { setSatelliteTimeStamp } from "../mapstyle/satellite-image";
import { isEqual, throttle } from 'lodash';
import { updateImageMapSources } from "../mapstyle/images";

const mapContainer: ShallowRef<null | HTMLElement> = shallowRef(null);
const map: ShallowRef<null | Map> = shallowRef(null);

const modelRunVectorLayers = reactive<Set<string>>(new Set());

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
    const regionIds = state.filters.regions ? state.filters.regions.map((region) => state.regionMap[region].id) : [];

    map.value = markRaw(
      new Map({
        container: mapContainer.value,
        style: style(state.timestamp, {
          groundTruthPattern: false,
          otherPattern: false,
        },
          state.satellite,
          state.enabledSiteImages,
          state.siteOverviewSatSettings,
          Array.from(modelRunVectorLayers),
          regionIds,
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
    if (map.value) {
    const editPolygon = useEditPolygon(map.value);
    editPolygon.initialize();
    // Having an issue with the selectedPoints Ref, although it is the true type.
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    state.editGeoJSON = editPolygon;
  }
  }
});

onUnmounted(() => {
  map.value?.remove();
});
const throttledSetSatelliteTimeStamp = throttle(setSatelliteTimeStamp, 300);

watch([() => state.timestamp, () => state.filters, () => state.satellite, () => state.filters.scoringColoring,
() => state.satellite.satelliteSources, () => state.enabledSiteImages, () => state.filters.hoverSiteId,
() => state.modelRuns, () => state.openedModelRuns, () => state.filters.proposals, () => state.filters.randomKey, () => state.filters.editingGeoJSONSiteId], (newVals, oldVals) => {

  if (state.satellite.satelliteImagesOn) {
    throttledSetSatelliteTimeStamp(state, filteredSatelliteTimeList.value);
  }

  const newFilters = newVals[1];
  const oldFilters = oldVals[1];

  // Clear layers on region change
  if (!isEqual(newFilters.regions, oldFilters.regions)) {
    modelRunVectorLayers.clear();
  }

  const openedModelRunIds = state.modelRuns.filter((m) => state.openedModelRuns.has(m.key)).map((m) => m.id);
  // Add in grounTruth for proposals if they aren't in the model-run list.
  state.filters.configuration_id?.forEach((item) => {
   if (!openedModelRunIds.includes(item)) {
    openedModelRunIds.push(item);
   }
  });

  // Add opened model runs to list of vector tile layers
  openedModelRunIds.forEach((m) => { modelRunVectorLayers.add(m) })

  const regionIds = state.filters.regions ? state.filters.regions.map((region) => state.regionMap[region].id) : [];

  if (map.value) {
    updateImageMapSources(state.timestamp, state.enabledSiteImages, state.siteOverviewSatSettings, map.value )
  }
  map.value?.setStyle(
    style(state.timestamp, state.filters, state.satellite, state.enabledSiteImages, state.siteOverviewSatSettings, Array.from(modelRunVectorLayers), regionIds, state.filters.randomKey),
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
    if (state.filters.showText) {
      setFilter(`observations-text-${id}`, observationFilter);
    }
  })

  setPopupEvents(map);

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
  height: 100%;
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

/* hides the editing controls in the viewer */
.mapboxgl-ctrl-group {
  display: none;
}
</style>
