<script setup lang="ts">
import ModelRunList from "./ModelRunList.vue";
import TimeSlider from "./TimeSlider.vue";
import PerformerFilter from "./filters/PerformerFilter.vue";
import FilterCheckBox from "./FilterCheckBox.vue";
import RegionFilter from "./filters/RegionFilter.vue";
import { state } from "../store";
import { ref, watch } from "vue";
import type { Performer, QueryArguments, Region } from "../client";
import type { Ref } from "vue";

const timemin = ref(Math.floor(new Date(0).valueOf() / 1000));
const queryFilters: Ref<QueryArguments> = ref({});

const selectedPerformer: Ref<Performer | null> = ref(null);
const selectedRegion: Ref<Region | null> = ref(null);
const groundTruth = ref(false);
watch(selectedPerformer, (val) => {
  queryFilters.value = { ...queryFilters.value, performer: val?.short_code };
  state.filters = {
    ...state.filters,
    performer_id: val?.id === undefined ? undefined : [val.id],
  };
});
watch(selectedRegion, (val) => {
  queryFilters.value = { ...queryFilters.value, region: val?.name };
  state.filters = {
    ...state.filters,
    region_id: val?.id === undefined ? undefined : [val.id],
  };
});
watch(groundTruth, (val) => {
  if (val) {
    queryFilters.value = { ...queryFilters.value, groundtruth: true };
    state.filters = { ...state.filters, groundtruth: true };
  } else {
    queryFilters.value = { ...queryFilters.value, groundtruth: undefined };
    state.filters = { ...state.filters, groundtruth: undefined };
  }
});
</script>

<template>
  <div class="relative">
    <div class="fixed h-screen w-80 pt-2 pb-2 pl-2">
      <div
        class="relative h-full overflow-hidden rounded-xl bg-white drop-shadow-2xl"
      >
        <div
          class="relative rounded-t-xl bg-gray-100 p-4 text-center text-sm font-light"
        >
          <img
            class="mx-auto pb-4"
            src="../assets/logo.svg"
            alt="Resonant GeoData"
            draggable="false"
          />
          <TimeSlider :min="timemin" :max="Math.floor(Date.now() / 1000)" />
          {{ new Date(state.timestamp * 1000).toLocaleString() }}
        </div>
        <div
          class="flex flex-nowrap gap-2 overflow-x-scroll border-t border-gray-300 bg-gray-100 p-2"
        >
          <PerformerFilter v-model="selectedPerformer" />
          <RegionFilter v-model="selectedRegion" />
          <FilterCheckBox v-model="groundTruth" label="Ground Truth" />
        </div>

        <ModelRunList
          :filters="queryFilters"
          @update:timerange="
            (timerange) => {
              if (timerange !== null) {
                timemin = timerange.min;
              }
            }
          "
        />
      </div>
    </div>
  </div>
</template>
