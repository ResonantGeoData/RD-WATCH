<script setup lang="ts">
import ModelRunList from "./ModelRunList.vue";
import TimeSlider from "./TimeSlider.vue";
import PerformerFilter from "./filters/PerformerFilter.vue";
import RegionFilter from "./filters/RegionFilter.vue";
import SettingsPanel from "./SettingsPanel.vue";
import { filteredSatelliteTimeList, state } from "../store";
import { computed, onMounted, ref, watch } from "vue";
import { ApiService, Performer, QueryArguments, Region } from "../client";
import type { Ref } from "vue";
import { changeTime } from "../interactions/timeStepper";

const timemin = ref(Math.floor(new Date(0).valueOf() / 1000));

const page = ref<number>(1);

const queryFilters = computed<QueryArguments>(() => ({
  page: page.value,
  performer: selectedPerformer.value.map((item) => item.short_code),
  region: selectedRegion.value,
}));

const selectedPerformer: Ref<Performer[]> = ref([]);
const selectedRegion: Ref<Region | undefined> = ref(undefined);
const drawSiteOutline: Ref<boolean> = ref(false);
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

const updateRegion = (val?: Region) => {
  page.value = 1;
  if (selectedRegion.value === undefined) {
    state.satellite.satelliteImagesOn = false;
    state.enabledSiteObservations = [];
    state.selectedObservations = [];
  }
  state.filters = {
    ...state.filters,
    regions: val === undefined ? undefined : [val],
  };
};
watch(drawSiteOutline, (val) => {
  state.filters = { ...state.filters, drawSiteOutline: val };
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


function nextPage() {
  page.value += 1;
}

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
const scoringApp = computed(()=> ApiService.apiPrefix.includes('scoring'));

const toggleGroundTruth = async () => {
  if (scoringApp.value) { 
    const val = !state.filters.drawGroundTruth;
    state.filters = { ...state.filters, drawGroundTruth: val };
  } else {
    // We need to find the ground-truth model and add it to the visible items
    const request = await ApiService.getModelRuns({
      limit: 10,
      performer: queryFilters.value.performer,
      region: queryFilters.value.region,
      groundtruth: true
    });
    if (request.items.length) {
      const id = request.items[0].id;
      if (!state.filters.drawGroundTruth) {
        if (state.openedModelRuns) {
          state.openedModelRuns.add(id);
        }
        const configuration_id = Array.from(state.openedModelRuns);
        state.filters = { ...state.filters, configuration_id};
        state.filters = { ...state.filters, drawGroundTruth: true };
      }
      else if (state.filters.drawGroundTruth) {
        if (state.openedModelRuns) {
          if (state.openedModelRuns.has(id)) {
            state.openedModelRuns.delete(id);
          }
        }
        const configuration_id = Array.from(state.openedModelRuns);
        state.filters = { ...state.filters, configuration_id};
        state.filters = { ...state.filters, drawGroundTruth: false };
      }
    }
  }
}

const toggleText = () => {
  const val = !state.filters.showText;
  state.filters = { ...state.filters, showText: val };
}

const toggleObs = () => {
  const val = !state.filters.drawObservations;
  state.filters = { ...state.filters, drawObservations: val };
}

const toggleSites = () => {
  const val = !state.filters.drawSiteOutline;
  state.filters = { ...state.filters, drawSiteOutline: val };
}

const toggleRegion = () => {
  const val = !state.filters.drawRegionPoly;
  state.filters = { ...state.filters, drawRegionPoly: val };
}

const toggleScoring = () => {
  const val = state.filters.scoringColoring ? undefined : 'simple';
  state.filters = { ...state.filters, scoringColoring: val };
}


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
        <img
          class="mx-auto pb-4"
          src="../assets/logo.svg"
          alt="Resonant GeoData"
          draggable="false"
        >
      </v-row>
      <v-row>
        <TimeSlider
          :min="timemin"
          :max="Math.floor(Date.now() / 1000)"
        />
      </v-row>
      <v-row
        align="center"
        justify="center"
      >
        <div
          style="min-width:185px; max-width: 185px;"
        >
          {{ new Date(state.timestamp * 1000).toLocaleString() }}
        </div>
      </v-row>
      <v-row
        dense
        align="center"
        class="py-2"
      >
        <v-tooltip
          open-delay="100"
          location="top"
        >
          <template #activator="{ props:subProps }">
            <v-chip
              density="compact"
              v-bind="subProps"
              size="small"
              :color="state.filters.drawObservations ? 'rgb(37, 99, 235)' : 'black'"
              :variant="state.filters.drawObservations ? 'elevated' : 'outlined'"
              class="mx-1"
              @click="toggleObs()"
            >
              Obs
            </v-chip>
          </template>
          <span>Toggle Site Observations on/off</span>
        </v-tooltip>
        <v-tooltip
          open-delay="100"
          location="top"
        >
          <template #activator="{ props:subProps }">
            <v-chip
              density="compact"
              v-bind="subProps"
              size="small"
              :color="state.filters.drawSiteOutline ? 'rgb(37, 99, 235)' : 'black'"
              :variant="state.filters.drawSiteOutline ? 'elevated' : 'outlined'"
              class="mx-1"
              @click="toggleSites()"
            >
              Site
            </v-chip>
          </template>
          <span> Toggle Site Outlines On/Off</span>
        </v-tooltip>

        <v-tooltip
          open-delay="100"
          location="top"
        >
          <template #activator="{ props:subProps }">
            <v-chip
              v-if="state.filters.regions?.length"
              v-bind="subProps"
              density="compact"
              :color="state.filters.drawGroundTruth ? 'rgb(37, 99, 235)' : 'black'"
              size="small"
              :variant="state.filters.drawGroundTruth ? 'elevated' : 'outlined'"
              class="mx-1"
              @click="toggleGroundTruth()"
            >
              GT
            </v-chip>
          </template>
          <span>Toggle associated Ground Truth On/Off</span>
        </v-tooltip>
        <v-tooltip
          open-delay="100"
          location="top"
        >
          <template #activator="{ props:subProps }">
            <v-chip
              v-bind="subProps"
              density="compact"
              size="small"
              :color="state.filters.drawRegionPoly ? 'rgb(37, 99, 235)' : 'black'"
              :variant="state.filters.drawRegionPoly ? 'elevated' : 'outlined'"
              class="mx-1"
              @click="toggleRegion()"
            >
              Region
            </v-chip>
          </template>
          <span>Toggle Region Polygons On/Off</span>
        </v-tooltip>
        <v-tooltip
          v-if="scoringApp && state.filters.drawSiteOutline"
          open-delay="100"
          location="top"
        >
          <template #activator="{ props:subProps }">
            <v-chip
              v-bind="subProps"
              density="compact"
              size="small"
              :color="state.filters.scoringColoring ? 'rgb(37, 99, 235)' : 'black'"
              :variant="state.filters.scoringColoring ? 'elevated' : 'outlined'"
              class="mx-1"
              @click="toggleScoring()"
            >
              Scores
            </v-chip>
          </template>
          <span>Toggle Region Polygons On/Off</span>
        </v-tooltip>
        <v-spacer />
        <v-btn
          variant="text"
          density="compact"
          class="pa-0 ma-0"
          :class="{
            'animate-flicker': state.satellite.loadingSatelliteImages,
          }"
          :color="imagesOn ? 'rgb(37, 99, 235)' : 'black'"
          :disabled="selectedRegion === null || (filteredSatelliteTimeList.length === 0 && state.satellite.satelliteSources.length !== 0)"
          icon="mdi-image"
          @click="imagesOn = selectedRegion !== null && (filteredSatelliteTimeList.length !== 0 || state.satellite.satelliteSources.length === 0) ? !imagesOn : imagesOn"
        />
        <v-btn
          :color="state.filters.showText ? 'rgb(37, 99, 235)' : 'gray'"
          variant="text"
          density="compact"
          icon="mdi-format-text"
          @click="toggleText()"
        />

        <v-btn
          :color="expandSettings ? 'rgb(37, 99, 235)' : 'gray'"
          variant="text"
          density="compact"
          icon="mdi-cog"
          @click="expandSettings = !expandSettings"
        />
        <v-btn
          :color="state.mapLegend ? 'rgb(37, 99, 235)' : 'gray'"
          variant="text"
          density="compact"
          icon="mdi-map-legend"
          @click="state.mapLegend = !state.mapLegend"
        />
      </v-row>
      <v-row
        dense
        class="mt-3"
      >
        <PerformerFilter
          v-model="selectedPerformer"
          class="pr-2"
          cols="6"
        />
        <RegionFilter
          v-model="selectedRegion"
          cols="6"
          @update:model-value="updateRegion($event)"
        />
      </v-row>
      <SettingsPanel v-if="expandSettings" />
    </div>
    <v-row
      v-if="!expandSettings"
      dense
      class="modelRuns"
    >
      <ModelRunList
        :filters="queryFilters"
        class="flex-grow-1"
        @next-page="nextPage"
        @update:timerange="
          (timerange) => {
            if (timerange !== null) {
              timemin = timerange.min;
              state.timeMin = timemin;
            }
          }
        "
      />
    </v-row>
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
</style>
