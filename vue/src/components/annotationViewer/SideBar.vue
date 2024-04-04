<script setup lang="ts">
import ModelRunList from "../ModelRunList.vue";
import TimeSlider from "../TimeSlider.vue";
import PerformerFilter from "../filters/PerformerFilter.vue";
import RegionFilter from "../filters/RegionFilter.vue";
import { filteredSatelliteTimeList, state } from "../../store";
import { computed, onMounted, ref, watch } from "vue";
import type { Performer, QueryArguments, Region } from "../../client";
import type { Ref } from "vue";
import { changeTime } from "../../interactions/timeStepper";

const timemin = ref(Math.floor(new Date(0).valueOf() / 1000));

const queryFilters = computed<QueryArguments>(() => ({
  performer: selectedPerformer.value.map((item) => item.short_code),
  region: selectedRegion.value,
}));

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

const groundTruthPattern = computed({
  get() {
    return state.filters.groundTruthPattern || false;
  },
  set(val: boolean) {
    state.filters = { ...state.filters, groundTruthPattern: val };
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

const imagesOn = computed({
  get() {
    return state.satellite.satelliteImagesOn || false;
  },
  set(val: boolean) {
    state.satellite = { ...state.satellite, satelliteImagesOn: val };
  },
});

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
          src="../../assets/logo.svg"
          alt="Resonant GeoData"
          draggable="false"
        >
      </v-row>
      <v-row>
        <TimeSlider
          :min="timemin || 0"
          :max="Math.floor(Date.now() / 1000)"
        />
      </v-row>
      <v-row class="mt-2">
        <v-spacer />
        <v-btn
          variant="tonal"
          density="compact"
          class="pa-0 ma-1 sidebar-icon"
          :color="groundTruthPattern ? 'primary' : 'black'"
          @click="groundTruthPattern = !groundTruthPattern"
        >
          <v-icon>mdi-gradient-horizontal</v-icon>
        </v-btn>
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
        <v-btn
          :color="state.mapLegend ? 'primary' : 'gray'"
          variant="tonal"
          density="compact"
          class="pa-0 ma-1 sidebar-icon"
          @click="state.mapLegend = !state.mapLegend"
        >
          <v-icon>mdi-map-legend</v-icon>
        </v-btn>
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
        />
      </v-row>
    </div>
    <v-row
      dense
      class="modelRuns"
    >
      <ModelRunList
        :filters="queryFilters"
        class="flex-grow-1"
        compact
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

.sidebar-icon {
  min-width: 40px;
  min-height: 40px;;
}

</style>
