<script setup lang="ts">
import ModelRunList from "../ModelRunList.vue";
import TimeSlider from "../TimeSlider.vue";
import PerformerFilter from "../filters/PerformerFilter.vue";
import RegionFilter from "../filters/RegionFilter.vue";
import { state } from "../../store";
import { computed, onMounted, ref, watch } from "vue";
import type { Performer, QueryArguments, Region } from "../../client";
import type { Ref } from "vue";
import { changeTime } from "../../interactions/timeStepper";

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
    scoringColoring: null,
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
    scoringColoring: null,
  };
};
watch(drawSiteOutline, (val) => {
  state.filters = { ...state.filters, drawSiteOutline: val, scoringColoring: null };
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

</script>

<template>
  <v-card
    class="pa-5 overflow-y-hidden"
    style="max-height:100vh; min-height:100vh;"
  >
    <div>
      <v-row>
        <TimeSlider
          :min="timemin || 0"
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
    </div>
    <v-row
      dense
      class="modelRuns"
    >
      <ModelRunList
        :filters="queryFilters"
        class="flex-grow-1"
        compact
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
