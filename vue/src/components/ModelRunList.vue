<script setup lang="ts">
import ModelRunDetail from "./ModelRunDetail.vue";
import type { ModelRunList } from "../client/models/ModelRunList";
import {
  CancelError,
  CancelablePromise,
  ModelRun,
  QueryArguments,
} from "../client";
import { computed, ref, watch, watchEffect } from "vue";
import type { Ref } from "vue";
import { ApiService } from "../client";
import { state } from "../store";
import { LngLatBounds } from "maplibre-gl";
import { hoveredInfo } from "../interactions/popup";
const limit = 10;
interface KeyedModelRun extends ModelRun {
  key: string;
}

const props = defineProps<{
  filters: QueryArguments;
}>();

const emit = defineEmits<{
  (e: "update:timerange", timerange: ModelRun["timerange"]): void;
  (e: "nextPage"): void;
}>();

const modelRuns: Ref<KeyedModelRun[]> = ref([]);
const openedModelRuns: Ref<Set<KeyedModelRun["key"]>> = ref(new Set());
const resultsBoundingBox = ref({
  xmin: -180,
  ymin: -90,
  xmax: 180,
  ymax: 90,
});
const totalModelRuns = ref(1);
const loading = ref(false);
const satelliteRegionTooLarge = ref(false);

let request: CancelablePromise<ModelRunList> | undefined;

async function loadMore() {
  loading.value = true;
  if (request !== undefined) {
    console.log("Cancelling request");
    request.cancel();
  }
  request = ApiService.getModelRuns({
    limit,
    ...props.filters,
  });
  try {
    const modelRunList = await request;
    request = undefined;
    loading.value = false;
    totalModelRuns.value = modelRunList.count;

    // sort list to show ground truth near the top
    const modelRunResults = modelRunList.results.sort((a, b) =>
      b.parameters["ground_truth"] === true ? 1 : -1
    );
    const keyedModelRunResults = modelRunResults.map((val, i) => {
      return {
        ...val,
        key: `${val.id}|${i + modelRuns.value.length}`,
      };
    });

    // If a bounding box was provided for this model run list, zoom the camera to it.
    if (modelRunList.bbox) {
      const bounds = new LngLatBounds();
      modelRunList.bbox.coordinates
        .flat()
        .forEach((c) => bounds.extend(c as [number, number]));
      const bbox = {
        xmin: bounds.getWest(),
        ymin: bounds.getSouth(),
        xmax: bounds.getEast(),
        ymax: bounds.getNorth(),
      };
      resultsBoundingBox.value = bbox;
      getSatelliteTimestamps(modelRunList)
      state.bbox = bbox;
    } else if (!state.filters.region_id?.length) {
      const bbox = {
        xmin: -180,
        ymin: -90,
        xmax: 180,
        ymax: 90,
      };
      state.bbox = bbox;
    }

    // If we're on page 1, we *might* have switched to a different filter/grouping in the UI,
    // meaning we would need to clear out any existing results.
    // To account for this, just set the array to the results directly instead of concatenating.
    if (props.filters.page === 1) {
      modelRuns.value = keyedModelRunResults;
    } else {
      modelRuns.value = modelRuns.value.concat(keyedModelRunResults);
    }
    emit("update:timerange", modelRunList["timerange"]);
  } catch (e) {
    if (e instanceof CancelError) {
      console.warn(e);
    } else {
      throw e;
    }
  }
}

/**
 * Set the camera bounds/viewport based on the currently selected model run(s).
 */
function updateCameraBounds(filtered = true) {
  const bounds = new LngLatBounds();
  let list = modelRuns.value;
  if (filtered) {
    list = modelRuns.value.filter((modelRun) =>
      openedModelRuns.value.has(modelRun.key)
    );
  }
  if (
    !state.settings.autoZoom &&
    state.filters.region_id &&
    state.filters.region_id?.length > 0
  ) {
    return;
  }
  list.forEach((modelRun) => {
    modelRun.bbox?.coordinates
      .flat()
      .forEach((c) => bounds.extend(c as [number, number]));
  });
  if (bounds.isEmpty()) {
    const bbox = {
      xmin: -180,
      ymin: -90,
      xmax: 180,
      ymax: 90,
    };
    state.bbox = bbox;
  } else {
    state.bbox = {
      xmin: bounds.getWest(),
      ymin: bounds.getSouth(),
      xmax: bounds.getEast(),
      ymax: bounds.getNorth(),
    };
  }
}

const loadingSatelliteTimestamps = ref(false);

async function getSatelliteTimestamps(modelRun: ModelRunList, force=false) {
  satelliteRegionTooLarge.value = false;
  loadingSatelliteTimestamps.value = true;
  state.satellite.satelliteTimeList = [];
  const bbox = modelRun.bbox?.coordinates[0];
  if (bbox && !force) {
    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    (bbox as []).forEach((item: [number, number]) => {
      minX = Math.min(minX, item[1]);
      minY = Math.min(minY, item[0]);
      maxX = Math.max(maxX, item[1]);
      maxY = Math.max(maxY, item[0]);
    })
    const xSize = maxX - minX;
    const ySize = maxY - minY;
    if (xSize > 1 || ySize > 1) {
      loadingSatelliteTimestamps.value = false;
      satelliteRegionTooLarge.value = true;
      return;
    }
  }
  const results = await ApiService.getAllSatelliteTimestamps(
      'S2', 'visual','2A', modelRun.timerange?.min, modelRun.timerange?.max, modelRun.bbox?.coordinates[0] as []);

  loadingSatelliteTimestamps.value = false;
  state.satellite.satelliteTimeList = results.filter((item) => item.source === 'WorldView');
  state.satellite.satelliteBounds = modelRun.bbox?.coordinates[0] as [];
}

function handleToggle(modelRun: KeyedModelRun) {
  if (openedModelRuns.value.has(modelRun.key)) {
    openedModelRuns.value.delete(modelRun.key);
  } else {
    openedModelRuns.value.add(modelRun.key);
  }

  if (openedModelRuns.value.size > 0) {
    // Only move camera if we're *not* currently filtering by region
    updateCameraBounds();
    const configurationIds: Set<number> = new Set();
    const regionIds: Set<number> = new Set();
    modelRuns.value
      .filter((modelRun) => openedModelRuns.value.has(modelRun.key))
      .map((modelRun) => {
        configurationIds.add(modelRun.id);
        if (modelRun.region) {
          regionIds.add(modelRun.region?.id);
        }
      });
    state.filters = {
      ...state.filters,
      configuration_id: Array.from(configurationIds),
      region_id: Array.from(regionIds),
    };
  } else {
    state.filters = {
      ...state.filters,
      configuration_id: undefined,
    };
    updateCameraBounds(false);
  }
}

async function handleScroll(event: Event) {
  const target = event.target as HTMLElement;

  // If the user has scrolled to the bottom of the list AND there are still more model runs to
  // fetch, bump the current page to trigger the loadMore function via a watcher.
  const heightPosCheck = Math.floor(target.scrollHeight - target.scrollTop) <= target.clientHeight;
  if (!loading.value && heightPosCheck && modelRuns.value.length < totalModelRuns.value) {
    if (props.filters.page !== undefined && Math.ceil(totalModelRuns.value / limit) > props.filters.page ) {
      emit("nextPage");
    }
  }
}

const hasSatelliteImages = computed(() => state.satellite.satelliteTimeList.length);

watchEffect(loadMore);
watch([() => props.filters.region, () => props.filters.performer], () => {
  openedModelRuns.value.clear();
  state.filters = {
    ...state.filters,
    configuration_id: [],
  };
});
</script>

<template>
  <div class="flex flex-row bg-gray-100">
    <span
      v-if="!loading && !loadingSatelliteTimestamps"
      style="font-size: 0.75em"
      class="badge-accent badge ml-2"
    >{{ totalModelRuns }} {{ totalModelRuns > 1 ? "Runs" : "Run" }}</span>
    <span
      v-if="!loading && !loadingSatelliteTimestamps && hasSatelliteImages&& !state.satellite.satelliteImagesOn && state.filters.region_id?.length"
      style="font-size: 0.75em"
      class="badge-secondary badge ml-2"
    >{{ hasSatelliteImages }} {{ hasSatelliteImages > 1 ? "Image Timestamps" : "Image Timestamp" }}</span>
    <span
      v-else-if="!loading && !loadingSatelliteTimestamps && state.satellite.satelliteTimeStamp && state.satellite.satelliteImagesOn && !satelliteRegionTooLarge"
      style="font-size: 0.75em"
      class="badge-secondary badge ml-2"
    >Satellite Time: {{ state.satellite.satelliteTimeStamp }} - {{ state.satellite.satelliteTimeSource }}</span>
    <div
      v-if="loading"
      class="px-2"
      style="width: 100%"
    >
      <b>ModelRun</b>
      <progress class="progress progress-primary" />
    </div>
    <div
      v-if="loadingSatelliteTimestamps"
      class="px-2"
      style="width: 100%"
    >
      <b>Satellite Timestamps</b>
      <progress class="progress progress-primary" />
    </div>
  </div>
  <div v-if="state.satellite.loadingSatelliteImages">
    <progress class="progress h-1 progress-primary" />
  </div>
  <div
    v-if="!loading && state.filters.region_id?.length && satelliteRegionTooLarge"
    style="font-size: 0.75em"
    class=""
  >
    <div class="alert alert-warning shadow-lg">
      <div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="stroke-current flex-shrink-0 h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
        ><path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        /></svg>
        <span>    Region is Too Large to efficiently get Images: 
        </span>
        <div class="flex-none">
          <button
            class="btn btn-xs btn-primary"
            @click="satelliteRegionTooLarge = false"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  </div>
  <div
    class="flex flex-col gap-2 overflow-y-scroll p-2"
    @scroll="handleScroll"
  >
    <ModelRunDetail
      v-for="modelRun in modelRuns"
      :key="modelRun.key"
      :model-run="modelRun"
      :open="openedModelRuns.has(modelRun.key)"
      :class="{
        outlined: hoveredInfo.includes(
          `${modelRun.id}_${modelRun.region?.id}_${modelRun.performer.id}`
        ),
      }"
      @toggle="() => handleToggle(modelRun)"
    />
  </div>
</template>

<style scoped>
.outlined {
  background-color: orange;
  border: 2px solid orange;
}
</style>
