<script setup lang="ts">
import ModelRunList from "./ModelRunList.vue";
import TimeSlider from "./TimeSlider.vue";
import PerformerFilter from "./filters/PerformerFilter.vue";
import RegionFilter from "./filters/RegionFilter.vue";
import { Cog6ToothIcon, PhotoIcon } from "@heroicons/vue/24/solid";
import SettingsPanel from "./SettingsPanel.vue";
import { filteredSatelliteTimeList, state } from "../store";
import { computed, onMounted, ref, watch } from "vue";
import type { Performer, QueryArguments, Region } from "../client";
import type { Ref } from "vue";
import { changeTime } from "../interactions/timeStepper";

const timemin = ref(Math.floor(new Date(0).valueOf() / 1000));
const queryFilters: Ref<QueryArguments> = ref({ page: 1 });

const selectedPerformer: Ref<Performer | null> = ref(null);
const selectedRegion: Ref<Region | null> = ref(null);
const showSiteOutline: Ref<boolean> = ref(false);
watch(selectedPerformer, (val) => {
  queryFilters.value = {
    ...queryFilters.value,
    performer: val?.short_code,
    page: 1,
  };
  state.filters = {
    ...state.filters,
    performer_id: val?.id === undefined ? undefined : [val.id],
  };
});
watch(selectedRegion, (val) => {
  queryFilters.value = { ...queryFilters.value, region: val?.name, page: 1 };
  if (selectedRegion.value === null) {
    state.satellite.satelliteImagesOn = false;
    state.enabledSiteObservations = [];
    state.selectedObservations = [];
  }
  state.filters = {
    ...state.filters,
    region_id: val?.id === undefined ? undefined : [val.id],
  };
});
watch(showSiteOutline, (val) => {
  state.filters = { ...state.filters, showSiteOutline: val };
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
  queryFilters.value = {
    ...queryFilters.value,
    page: (queryFilters.value.page || 0) + 1,
  };
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

</script>

<template>
  <v-card
    class="pa-5"
    style="max-height:100vh; min-height:100vh; overflow-y: hidden;"
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
        <div> {{ new Date(state.timestamp * 1000).toLocaleString() }}</div>
      </v-row>
      <v-row dense>
        <v-spacer />
        <PhotoIcon 
          class="h-5 mt-0.5"
          :class="{
            'animate-flicker': state.satellite.loadingSatelliteImages,
            'text-blue-600': imagesOn,
            'hover': selectedRegion !== null && (filteredSatelliteTimeList.length !== 0 || state.satellite.satelliteSources.length === 0),
            'text-gray-400': selectedRegion === null || (filteredSatelliteTimeList.length === 0 && state.satellite.satelliteSources.length !== 0),
          }"
          @click="imagesOn = selectedRegion !== null && (filteredSatelliteTimeList.length !== 0 || state.satellite.satelliteSources.length === 0) ? !imagesOn : imagesOn"
        />
        <Cog6ToothIcon
          class="hover h-5 text-blue-600 mt-0.5"
          @click="expandSettings = !expandSettings"
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
        style="flex-grow: 1;"
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
.modelRuns {
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
