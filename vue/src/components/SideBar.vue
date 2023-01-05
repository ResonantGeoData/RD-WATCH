<script setup lang="ts">
import ModelRunList from "./ModelRunList.vue";
import TimeSlider from "./TimeSlider.vue";
import PerformerFilter from "./filters/PerformerFilter.vue";
import RegionFilter from "./filters/RegionFilter.vue";
import { state } from "../store";
import { ref, watch } from "vue";
import type { Performer, QueryArguments, Region } from "../client";
import type { Ref } from "vue";

const timemin = ref(Math.floor(new Date(0).valueOf() / 1000));
const queryFilters: Ref<QueryArguments> = ref({ page: 1 });

const selectedPerformer: Ref<Performer | null> = ref(null);
const selectedRegion: Ref<Region | null> = ref(null);
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
  state.filters = {
    ...state.filters,
    region_id: val?.id === undefined ? undefined : [val.id],
  };
});

function nextPage() {
  queryFilters.value = {
    ...queryFilters.value,
    page: (queryFilters.value.page || 0) + 1,
  };
}
</script>

<template>
  <div class="fixed h-screen w-80 pt-2 pb-2 pl-2">
    <div
      class="flex h-full flex-col overflow-hidden rounded-xl bg-white drop-shadow-2xl"
    >
      <div class="bg-gray-100 p-4 text-center text-sm font-light">
        <img
          class="mx-auto pb-4"
          src="../assets/logo.svg"
          alt="Resonant GeoData"
          draggable="false"
        />
        <TimeSlider :min="timemin" :max="Math.floor(Date.now() / 1000)" />
        {{ new Date(state.timestamp * 1000).toLocaleString() }}
      </div>
      <div>
        <div
          class="flex flex-nowrap gap-2 overflow-x-scroll border-t border-gray-300 bg-gray-100 p-2"
        >
          <PerformerFilter v-model="selectedPerformer" />
          <RegionFilter v-model="selectedRegion" />
        </div>
      </div>

      <ModelRunList
        :filters="queryFilters"
        class="basis-full"
        @next-page="nextPage"
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
</template>
