<script setup lang="ts">
import ModelRunList from "./ModelRunList.vue";
import TimeSlider from "./TimeSlider.vue";
import PerformerFilter from "./filters/PerformerFilter.vue";
import RegionFilter from "./filters/RegionFilter.vue";
import ModeFilter from "./filters/ModeFilter.vue";
import SettingsPanel from "./SettingsPanel.vue";
import ErrorPopup from './ErrorPopup.vue';
import { filteredSatelliteTimeList, state } from "../store";
import { computed, onMounted, ref, watch } from "vue";
import { ApiService, Performer, QueryArguments, Region } from "../client";
import type { Ref } from "vue";
import { changeTime } from "../interactions/timeStepper";
import { useRoute } from "vue-router";

const timemin = ref(Math.floor(new Date(0).valueOf() / 1000));

const page = ref<number>(1);
const route = useRoute();
watch(() => route.path, (oldPath, newPath) => {
  if ((!oldPath.includes('/scoring') && newPath.includes('/scoring')) || (oldPath.includes('/scoring') && !newPath.includes('/scoring'))) {
    console.log(`Resetting path:  old:${oldPath}  new:${newPath}`);
    selectedPerformer.value = [];
    selectedRegion.value = undefined;
    state.enabledSiteObservations = [];
    state.selectedObservations = [];
    state.filters = {
    ...state.filters,
    regions: undefined,
    performer_ids: undefined,
  };

  }
});

const scoringApp = computed(()=> route.path.includes('scoring') && !route.path.includes('proposal'));


const queryFilters = computed<QueryArguments>(() => ({
  page: page.value,
  performer: selectedPerformer.value.map((item) => item.short_code),
  region: selectedRegion.value,
  mode: selectedMode.value,
}));

const selectedMode: Ref<string | undefined> = ref(undefined);
const selectedPerformer: Ref<Performer[]> = ref([]);
const selectedRegion: Ref<Region | undefined> = ref(undefined);
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

const updateMode = (mode?: string) => {
  page.value = 1;
  state.filters = {
    ...state.filters,
    mode: mode,
  };
};

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

const toggleText = () => {
  const val = !state.filters.showText;
  state.filters = { ...state.filters, showText: val };
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
        <ErrorPopup />
        <img
          height="50"
          class="mx-auto pb-4"
          src="../assets/logo.svg"
          alt="Resonant GeoData"
          draggable="false"
        >
      </v-row>
      <v-row dense>
        <v-spacer />
        <v-btn
          to="/"
          :color="!scoringApp? 'rgb(37, 99, 235)': ''"
          :theme="!scoringApp? 'dark': ''"
          size="x-small"
          class="mx-2"
        >
          RGD
        </v-btn>
        <v-btn
          to="/scoring"
          :color="scoringApp? 'rgb(37, 99, 235)': ''"
          :theme="scoringApp? 'dark': ''"
          size="x-small"
          class="mx-2"
        >
          Scoring
        </v-btn>
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
        <v-spacer />
        <v-btn
          variant="text"
          density="compact"
          class="pa-0 ma-0"
          :color="drawMap ? 'rgb(37, 99, 235)' : 'black'"
          icon="mdi-road"
          @click="drawMap = !drawMap"
        />
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
      <v-row
        v-if="ApiService.isScoring()"
        dense
      >
        <ModeFilter
          v-model="selectedMode"
          class="pr-2"
          @update:model-value="updateMode($event)"
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

</style>
