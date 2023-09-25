<script setup lang="ts">
import ModelRunDetail from "./ModelRunDetail.vue";
import type { ModelRunList } from "../client/models/ModelRunList";
import {
  CancelError,
  CancelablePromise,
  ModelRun,
  QueryArguments,
} from "../client";
import { computed, ref, watch, watchEffect, withDefaults } from "vue";
import { ApiService } from "../client";
import { filteredSatelliteTimeList, state } from "../store";
import type { KeyedModelRun } from '../store'
import { LngLatBounds } from "maplibre-gl";
import { hoveredInfo } from "../interactions/mouseEvents";
const limit = 10;

interface Props {
  filters: QueryArguments;
  compact?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  compact: false,
});

const emit = defineEmits<{
  (e: "update:timerange", timerange: ModelRun["timerange"]): void;
  (e: "nextPage"): void;
}>();

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
    request.cancel();
  }
  const { performer } = props.filters; // unwrap performer array
  request = ApiService.getModelRuns({
    limit,
    ...props.filters,
    performer,
    proposal: props.compact ? 'PROPOSAL' : undefined, // if compact we are doing proposal adjudication
  });
  try {
    const modelRunList = await request;
    request = undefined;
    loading.value = false;
    totalModelRuns.value = modelRunList.count;

    // sort list to show ground truth near the top
    console.log(modelRunList);
    const modelRunResults = modelRunList.results.sort((a, b) =>
      b.parameters["ground_truth"] === true ? 1 : -1
    );
    const keyedModelRunResults = modelRunResults.map((val, i) => {
      return {
        ...val,
        key: `${val.id}|${i + state.modelRuns.length}`,
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
      if (!props.compact) {
          getSatelliteTimestamps(modelRunList)
      }
      state.bbox = bbox;
    } else if (!state.filters.regions?.length) {
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
      state.modelRuns = keyedModelRunResults;
    } else {
      state.modelRuns = state.modelRuns.concat(keyedModelRunResults);
    }
    emit("update:timerange", modelRunList["timerange"]);
  } catch (e) {
    if (e instanceof CancelError) {
      console.log('Request has been cancelled');
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
  let list = state.modelRuns;
  if (filtered) {
    list = state.modelRuns.filter((modelRun) =>
      state.openedModelRuns.has(modelRun.key)
    );
  }
  if (
    !state.settings.autoZoom &&
    state.filters.regions &&
    state.filters.regions?.length > 0
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
  state.satellite.satelliteTimeList = results;
  state.satellite.satelliteBounds = modelRun.bbox?.coordinates[0] as [];
}

async function checkScores(modelRun: KeyedModelRun)  {
  let hasScores = false;
  try {
    //hasScores = await ApiService.hasScores(modelRun.id, modelRun.region?.id || 0)
  } catch (err) {
    hasScores = false;
  }
  const foundIndex = state.modelRuns.findIndex((item) => item === modelRun);
  if (hasScores) {
    // Do something to set the value on the keyed Model run
    if (foundIndex !== -1) {
      state.modelRuns[foundIndex].hasScores = true;
    }
  } else {
    state.modelRuns[foundIndex].hasScores = undefined;
  }
}

function handleToggle(modelRun: KeyedModelRun) {
  if (state.openedModelRuns.has(modelRun.key)) {
    state.openedModelRuns.delete(modelRun.key);
  } else {
    if (props.compact) {
      state.openedModelRuns.clear();
    }
    state.openedModelRuns.add(modelRun.key);
  }

  if (state.openedModelRuns.size > 0) {
    // Only move camera if we're *not* currently filtering by region
    updateCameraBounds();
    const configurationIds: Set<number> = new Set();
    const regions: Set<string> = new Set();
    state.modelRuns
      .filter((modelRun) => state.openedModelRuns.has(modelRun.key))
      .map((modelRun) => {
        configurationIds.add(modelRun.id);
        if (modelRun.region) {
          regions.add(modelRun.region);
        }
      });
    state.filters = {
      ...state.filters,
      configuration_id: Array.from(configurationIds),
      regions: Array.from(regions),
      scoringColoring: null,
    };
  } else {
    state.filters = {
      ...state.filters,
      configuration_id: undefined,
      scoringColoring: null,
    };
    updateCameraBounds(false);
  }
  if (modelRun.hasScores === undefined && modelRun.performer.short_code !== 'TE') {
    checkScores(modelRun);
  }
}

async function handleScroll(event: Event) {
  const target = event.target as HTMLElement;

  // If the user has scrolled to the bottom of the list AND there are still more model runs to
  // fetch, bump the current page to trigger the loadMore function via a watcher.
  const heightPosCheck = Math.floor(target.scrollHeight - target.scrollTop) <= target.clientHeight;
  if (!loading.value && heightPosCheck && state.modelRuns.length < totalModelRuns.value) {
    if (props.filters.page !== undefined && Math.ceil(totalModelRuns.value / limit) > props.filters.page ) {
      emit("nextPage");
    }
  }
}

const hasSatelliteImages = computed(() => filteredSatelliteTimeList.value.length);

watchEffect(loadMore);
watch([() => props.filters.region, () => props.filters.performer], () => {
  state.openedModelRuns.clear();
  state.filters = {
    ...state.filters,
    configuration_id: [],
    scoringColoring: null,
  };
});
</script>

<template>
  <div>
    <v-row v-if="!compact">
      <v-chip
        v-if="!loading && !loadingSatelliteTimestamps"
        style="font-size: 0.75em"
        label
        density="compact"
        color="green"
        class="ml-2"
      >
        {{ totalModelRuns }} {{ totalModelRuns > 1 ? "Runs" : "Run" }}
      </v-chip>
      <v-chip
        v-if="!loading && !loadingSatelliteTimestamps && hasSatelliteImages && !state.satellite.satelliteImagesOn && state.filters.regions?.length"
        style="font-size: 0.75em"
        label
        density="compact"
        color="pink"
        class="ml-2"
      >
        {{ hasSatelliteImages }} {{ hasSatelliteImages > 1 ? "Image Timestamps" : "Image Timestamp" }}
      </v-chip>
      <v-chip
        v-else-if="!loading && !loadingSatelliteTimestamps && state.satellite.satelliteTimeStamp && state.satellite.satelliteImagesOn && !satelliteRegionTooLarge"
        style="font-size: 0.75em"
        label
        density="compact"
        color="pink"
        class="ml-2"
      >
        Satellite Time: {{ state.satellite.satelliteTimeStamp }} - {{ state.satellite.satelliteTimeSource }}
      </v-chip>
      <div
        v-if="loading"
        class="px-2"
        style="width: 100%"
      >
        <b>ModelRun</b>
        <v-progress-linear indeterminate />
      </div>
      <div
        v-if="loadingSatelliteTimestamps"
        class="px-2"
        style="width: 100%"
      >
        <b>Satellite Timestamps</b>
        <v-progress-linear indeterminate />
      </div>
    </v-row>
    <div
      v-if="state.satellite.loadingSatelliteImages"
      class="mt-5"
    >
      <v-progress-linear
        indeterminate
        height="8"
        color="primary"
      />
    </div>
    <div
      v-if="!loading && state.filters.regions?.length && satelliteRegionTooLarge"
      class="mt-5"
      style="font-size: 0.75em"
    >
      <v-alert type="warning">
        <div>
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
      </v-alert>
    </div>
    <v-container
      class="overflow-y-auto p-5 mt-5"
      :class="{ modelRuns: !compact, compactModelRuns: compact}"
      @scroll="handleScroll"
    >
      <ModelRunDetail
        v-for="modelRun in state.modelRuns"
        :key="modelRun.key"
        :model-run="modelRun"
        :compact="compact"
        :open="state.openedModelRuns.has(modelRun.key)"
        :class="{
          outlined: hoveredInfo.region.includes(
            `${modelRun.id}_${modelRun.region}_${modelRun.performer.id}`
          ),
        }"
        @toggle="() => handleToggle(modelRun)"
      />
    </v-container>
  </div>
</template>

<style scoped>
.modelRuns {
  height: calc(100vh - 250px);
}
.compactModelRuns {
  height: calc(100vh - 150px);
}
.outlined {
  background-color: orange;
  border: 3px solid orange;
}
</style>
