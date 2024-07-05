<script setup lang="ts">
import ModelRunListVue from "./ModelRunList.vue";
import TimeSlider from "./TimeSlider.vue";
import PerformerFilter from "./filters/PerformerFilter.vue";
import EvalFilter from "./filters/EvalFilter.vue";
import RegionFilter from "./filters/RegionFilter.vue";
import ModeFilter from "./filters/ModeFilter.vue";
import SettingsPanel from "./SettingsPanel.vue";
import ErrorPopup from './ErrorPopup.vue';
import { filteredSatelliteTimeList, state } from "../store";
import { computed, onMounted, ref, watch } from "vue";
import { ApiService, Eval, Performer, QueryArguments, Region } from "../client";
import { ModelRunList } from "../client/models/ModelRunList";
import type { Ref } from "vue";
import { changeTime } from "../interactions/timeStepper";
import { useRoute } from "vue-router";
import ModeSelector from './ModeSelector.vue';

const timemin = ref(Math.floor(new Date(0).valueOf() / 1000));

const route = useRoute();
watch(() => route.path, (oldPath, newPath) => {
  if ((!oldPath.includes('/scoring') && newPath.includes('/scoring')) || (oldPath.includes('/scoring') && !newPath.includes('/scoring'))) {
    selectedPerformer.value = [];
    selectedRegion.value = undefined;
    state.enabledSiteImages = [];
    state.selectedSites = [];
    state.filters = {
    ...state.filters,
    regions: undefined,
    performer_ids: undefined,
  };

  }
});



const queryFilters = computed<QueryArguments>(() => ({
  performer: selectedPerformer.value.map((item) => item.short_code),
  region: selectedRegion.value,
  mode: selectedModes.value,
  eval: selectedEval.value,
  groundtruth: groundtruth.value,
}));

const selectedModes: Ref<string[]> = ref([]);
const groundtruth: Ref<boolean> = ref(false);
const selectedPerformer: Ref<Performer[]> = ref([]);
const selectedRegion: Ref<Region | undefined> = ref(undefined);
const selectedEval: Ref<Eval[]> = ref([]);
watch(selectedPerformer, (val) => {
  state.filters = {
    ...state.filters,
    performer_ids: !val.length ? undefined : val.map((item) => item.id),
  };
});
watch (() => state.filters.regions, () => {
  if (state.filters.regions?.length) {
    selectedRegion.value = state.filters.regions[0];
  }
});

watch(selectedRegion, () => {
  // Reset satellite time list when on other regions
  satelliteRegionTooLarge.value = false;
  state.satellite = { ...state.satellite, satelliteImagesOn: false, satelliteTimeList: []};
  state.filters = { ...state.filters, regions: selectedRegion.value ? [selectedRegion.value] : undefined };
});

const expandSettings = ref(false);

const imagesOn = computed({
  get() {
    return state.satellite.satelliteImagesOn || false;
  },
  set(val: boolean) {
    state.satellite = { ...state.satellite, satelliteImagesOn: val };
  },
});

const drawMap = computed({
  get() {
    return state.filters.drawMap || false;
  },
  set(val: boolean) {
    state.filters = { ...state.filters, drawMap: val };
  },
});

onMounted(() => {
  window.document.addEventListener('keydown', (event) => {
    if (event.code === 'ArrowLeft') {
      // Call function for left arrow key press
      changeTime(-1);
    } else if (event.code === 'ArrowRight') {
      // Call function for right arrow key press
      changeTime(1);
    }
  });
});

const toggleText = () => {
  const val = !state.filters.showText;
  state.filters = { ...state.filters, showText: val };
}

// Satellite downloading Variables
const currentModelRunList: Ref<ModelRunList | null> = ref(null);
const satelliteRegionTooLarge = ref(false);
const loadingSatelliteTimestamps = ref(false);
const askDownloadSatelliteTimestamps = ref(false);
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

const startLoadingSatelliteTimeStamps = async () => {
  askDownloadSatelliteTimestamps.value = false;
  if (currentModelRunList.value) {
    getSatelliteTimestamps(currentModelRunList.value);
  }
}

const satelliteLoadingColor = computed(() => {
  if (satelliteRegionTooLarge.value) {
    return 'warning'
  }
  if (loadingSatelliteTimestamps.value) {
    return 'primary';
  }
  return 'black'
})



</script>

<template>
  <v-card
    class="pa-5 overflow-y-hidden"
    style="max-height:100vh; min-height:100vh;"
  >
    <div>
      <v-row
        dense
      >
        <ErrorPopup />
        <img
          height="50"
          class="mx-auto pb-4"
          src="../assets/logo.svg"
          alt="Resonant GeoData"
          draggable="false"
        >
      </v-row>
      <mode-selector />
      <v-row>
        <TimeSlider
          :min="timemin"
          :max="Math.floor(Date.now() / 1000)"
        />
      </v-row>
      <v-row
        dense
        align="center"
        class="py-2"
      >
        <v-spacer />
        <v-btn
          variant="tonal"
          density="compact"
          class="pa-0 ma-1 sidebar-icon"
          :color="drawMap ? 'primary' : 'black'"
          @click="drawMap = !drawMap"
        >
          <v-icon>mdi-road</v-icon>
        </v-btn>
        <v-btn
          v-if="selectedRegion !== null && !(filteredSatelliteTimeList.length === 0 && state.satellite.satelliteSources.length !== 0)"
          variant="tonal"
          density="compact"
          class="pa-0 ma-1 sidebar-icon"
          :class="{
            'animate-flicker': state.satellite.loadingSatelliteImages,
          }"
          :color="imagesOn ? 'primary' : 'black'"
          :disabled="selectedRegion === null || (filteredSatelliteTimeList.length === 0 && state.satellite.satelliteSources.length !== 0)"
          @click="imagesOn = selectedRegion !== null && (filteredSatelliteTimeList.length !== 0 || state.satellite.satelliteSources.length === 0) ? !imagesOn : imagesOn"
        >
          <v-icon>mdi-image</v-icon>
        </v-btn>
        <v-tooltip v-else>
          <template #activator="{ props: props }">
            <v-btn
              variant="tonal"
              v-bind="props"
              :disabled="!selectedRegion"
              density="compact"
              :class="{
                'animate-flicker': loadingSatelliteTimestamps,
              }"
              class="pa-0 ma-1 sidebar-icon"
              :color="satelliteLoadingColor"
              @click="askDownloadSatelliteTimestamps = true"
            >
              <v-icon>mdi-satellite-variant</v-icon>
            </v-btn>
          </template>
          <v-alert
            v-if="!satelliteRegionTooLarge"
            type="warning"
            title="Download Region Satellite Timestamps"
            text="This is a long running process that could cause instability on the server.  Please only run this if you are sure you need to use the region satellite feature."
          />
          <v-alert
            v-else
            type="warning"
            title="Region Too Large to Download Timestamps"
            text="The Region is too large to download timestamps for."
          />
        </v-tooltip>
        <v-btn
          :color="state.filters.showText ? 'primary' : 'gray'"
          variant="tonal"
          class="pa-0 ma-1 sidebar-icon"
          density="compact"
          @click="toggleText()"
        >
          <v-icon>mdi-format-text</v-icon>
        </v-btn>
        <v-btn
          :color="state.mapLegend ? 'primary' : 'gray'"
          variant="tonal"
          class="pa-0 ma-1 sidebar-icon"
          density="compact"
          @click="state.mapLegend = !state.mapLegend"
        >
          <v-icon>mdi-map-legend</v-icon>
        </v-btn>
        <v-tooltip>
          <template #activator="{ props: props }">
            <v-btn
              variant="tonal"
              v-bind="props"
              density="compact"
              class="pa-0 ma-1 sidebar-icon"
              :color="groundtruth ? 'primary' : 'gray'"
              @click="groundtruth = !groundtruth"
            >
              <v-icon>mdi-check-decagram</v-icon>
            </v-btn>
          </template>
          <span> Toggle Ground Truth in the list</span>
        </v-tooltip>
        <v-btn
          :color="expandSettings ? 'primary' : 'gray'"
          variant="tonal"
          class="pa-0 ma-1 sidebar-icon"
          density="compact"
          @click="expandSettings = !expandSettings"
        >
          <v-icon>mdi-cog</v-icon>
        </v-btn>
      </v-row>
      <v-row
        dense
        class="mt-3"
      >
        <PerformerFilter
          v-model="selectedPerformer"
          cols="6"
          class="px-1"
          hide-details
        />
        <RegionFilter
          v-model="selectedRegion"
          cols="6"
          class="px-1"
          hide-details
        />
      </v-row>
      <v-row
        v-if="ApiService.isScoring()"
        class="pt-2"
        dense
      >
        <ModeFilter
          v-model="selectedModes"
          class="px-1"
          hide-details
        />
        <EvalFilter
          v-model="selectedEval"
          class="px-1"
          hide-details
        />
      </v-row>
    </div>
    <v-row
      dense
      class="modelRuns"
    >
      <SettingsPanel v-if="expandSettings" />
      <ModelRunListVue
        v-if="!expandSettings"
        :filters="queryFilters"
        class="flex-grow-1"
        @update:timerange="
          (timerange) => {
            if (timerange !== null) {
              timemin = timerange.min;
              state.timeMin = timemin;
            }
          }
        "
        @modelrunlist="currentModelRunList = $event"
      />
    </v-row>
    <v-dialog
      v-model="askDownloadSatelliteTimestamps"
      width="600"
    >
      <v-card>
        <v-card-title>Download Satellite Timestamps</v-card-title>
        <v-card-text>
          <v-alert type="warning">
            Downloading satellite timestamps can cause the server to become unstable.  Only use this feature if you need to view full region satellite images and realize that usage will impact other users on the server.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-row>
            <v-spacer />
            <v-btn
              color="error"
              class="mx-2"
              variant="tonal"
              @click="askDownloadSatelliteTimestamps = false"
            >
              Cancel
            </v-btn>
            <v-btn
              color="warning"
              class="mx-2"
              variant="tonal"
              @click="startLoadingSatelliteTimeStamps()"
            >
              Download
            </v-btn>
          </v-row>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<style scoped>

.hover:hover {
  cursor: pointer;
}
@keyframes flicker-animation {
  0% { opacity: 1; }
  50% { opacity: 0; }
  100% { opacity: 1; }
}

.animate-flicker {
  animation: flicker-animation 1s infinite;
}
.layer-button {
  border: 1px solid black;
  padding-top:5px;
  padding-bottom: 5px;
  margin-left: auto;
  margin-right: auto;
}

.layer-header {
  border: 2px solid black;
  border-bottom: 2px double black;
  padding-top:5px;
  padding-bottom: 5px;
  margin-left: auto;
  margin-right: auto;

}

.modelRuns {
  margin-top: 2em
}

.sidebar-icon {
  min-width: 40px;
  min-height: 40px;;
}
</style>
