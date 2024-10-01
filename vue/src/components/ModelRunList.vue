<script setup lang="ts">
import ModelRunCard from "./ModelRunCard.vue";
import type { ModelRunList } from "../client/models/ModelRunList";
import { ApiService, type QueryArguments } from "../client";
import { computed, onMounted, ref, watch, withDefaults } from "vue";
import { filteredSatelliteTimeList, queryModelRuns, state, updateCameraBoundsBasedOnModelRunList, updatePerformers, updateRegionList } from "../store";
import type { KeyedModelRun } from '../store'
import { hoveredInfo } from "../interactions/mouseEvents";
import UploadModelRun from './UploadModelRun.vue';
import { useRoute } from 'vue-router';

interface Props {
  filters: QueryArguments;
  compact?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  compact: false,
});

const emit = defineEmits<{
  (e: "modelrunlist", modelRunList: ModelRunList): void;
}>();

const totalModelRuns = computed(() => state.totalNumModelRuns);
const loading = computed(() => state.queryStates.loadModelRuns.inflightQueries > 0);
const satelliteRegionTooLarge = ref(false);

const route = useRoute();
const isAnnotatorMode = computed(() => {
  return route.fullPath.replace(/\/$/, '').endsWith('proposals')
});

async function loadModelRuns(type: 'firstPage' | 'nextPage') {
  const modelRunList = await queryModelRuns(type, props.filters, props.compact);
  emit('modelrunlist', modelRunList);
}

const loadingSatelliteTimestamps = ref(false);

const isScoring = computed(() => ApiService.isScoring());

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
  if (!loading.value && heightPosCheck) {
    loadModelRuns('nextPage');
  }
}

const refreshListings = () => {
  updatePerformers();
  updateRegionList();
  queryModelRuns('firstPage', props.filters);
};

const hasSatelliteImages = computed(() => filteredSatelliteTimeList.value.length);

watch([() => props.filters.region, () => props.filters.performer, () => props.filters.eval], () => {
  state.openedModelRuns.clear();
  state.filters = {
    ...state.filters,
    configuration_id: [],
  };
  loadModelRuns('firstPage');
});

onMounted(() => loadModelRuns('firstPage'));
</script>

<template>
  <div class="d-flex flex-column overflow-hidden">
    <div class="d-flex flex-wrap flex-grow-0">
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
    </div>
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
    <div class="d-flex justify-end flex-grow-0 pb-2">
      <upload-model-run
        v-if="!isScoring && !isAnnotatorMode"
        @upload="refreshListings"
      />
    </div>
    <v-container
      class="overflow-y-auto flex-grow-1 flex-shrink-1"
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
.outlined {
  background-color: orange;
  border: 3px solid orange;
}
</style>
