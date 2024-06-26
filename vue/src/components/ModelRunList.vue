<script setup lang="ts">
import ModelRunCard from "./ModelRunCard.vue";
import type { ModelRunList } from "../client/models/ModelRunList";
import { LngLatBounds } from "maplibre-gl";
import {
  CancelError,
  CancelablePromise,
  ModelRun,
  QueryArguments,
} from "../client";
import { computed, onMounted, ref, watch, withDefaults } from "vue";
import { ApiService } from "../client";
import { filteredSatelliteTimeList, state, updateCameraBoundsBasedOnModelRunList } from "../store";
import type { KeyedModelRun } from '../store'
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
  (e: "modelrunlist", modelRunList: ModelRunList): void;
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
const page = ref(1);

let request: CancelablePromise<ModelRunList> | undefined;

async function loadModelRuns() {
  loading.value = true;
  if (request !== undefined) {
    request.cancel();
  }
  const { mode, performer } = props.filters; // unwrap performer and mode arrays
  request = ApiService.getModelRuns({
    limit,
    ...props.filters,
    mode,
    performer,
    proposal: props.compact ? 'PROPOSAL' : undefined, // if compact we are doing proposal adjudication
  });
  try {
    const modelRunList = await request;
    request = undefined;
    loading.value = false;
    totalModelRuns.value = modelRunList.count;

    // sort list to show ground truth near the top
    const modelRunResults = modelRunList.items;
    const keyedModelRunResults = modelRunResults.map((val) => {
      return {
        ...val,
        key: `${val.id}`,
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
    if (page.value === 1) {
      state.modelRuns = keyedModelRunResults;
    } else {
      state.modelRuns = state.modelRuns.concat(keyedModelRunResults);
    }
    emit("update:timerange", modelRunList["timerange"]);
    emit("modelrunlist", modelRunList);
  } catch (e) {
    if (e instanceof CancelError) {
      console.log('Request has been cancelled');
    } else {
      throw e;
    }
  }
}


const loadingSatelliteTimestamps = ref(false);

function handleToggle(modelRun: KeyedModelRun) {
  if (state.selectedImageSite) {
    state.selectedImageSite = undefined;
  }
  if (state.openedModelRuns.has(modelRun.key)) {
    state.openedModelRuns.delete(modelRun.key);
    if (modelRun.groundTruthLink && state.groundTruthLinks[modelRun.id]) {
      delete state.groundTruthLinks[modelRun.id];
    }
  } else {
    if (props.compact) {
      state.openedModelRuns.clear();
    }
    state.openedModelRuns.add(modelRun.key);
    if (modelRun.groundTruthLink) {
      state.groundTruthLinks[modelRun.id] = modelRun.groundTruthLink;
    }

  }

  if (state.openedModelRuns.size > 0) {
    // Only move camera if we're *not* currently filtering by region
    updateCameraBoundsBasedOnModelRunList();
    const configurationIds: Set<string> = new Set();
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
    };
  } else {
    state.filters = {
      ...state.filters,
      configuration_id: undefined,
    };
    updateCameraBoundsBasedOnModelRunList(false);
  }
}

async function handleScroll(event: Event) {
  const target = event.target as HTMLElement;

  // If the user has scrolled to the bottom of the list AND there are still more model runs to
  // fetch, bump the current page to trigger the loadMore function via a watcher.
  const heightPosCheck = Math.floor(target.scrollHeight - target.scrollTop) <= target.clientHeight;
  if (!loading.value && heightPosCheck && state.modelRuns.length < totalModelRuns.value) {
    if (page.value !== undefined && Math.ceil(totalModelRuns.value / limit) > page.value ) {
      page.value += 1;
      loadModelRuns();
    }
  }
}

const hasSatelliteImages = computed(() => filteredSatelliteTimeList.value.length);

watch([() => props.filters.region, () => props.filters.performer, () => props.filters.eval], () => {
  page.value = 1;
  state.openedModelRuns.clear();
  state.filters = {
    ...state.filters,
    configuration_id: [],
  };
  loadModelRuns();
});

onMounted(() => loadModelRuns());
</script>

<template>
  <div>
    <v-row>
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
      <ModelRunCard
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
