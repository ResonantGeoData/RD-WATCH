<script setup lang="ts">
import EvaluationList from "./EvaluationList.vue";
import TimeSlider from "./TimeSlider.vue";
import { state } from "../store";
import { ApiService } from "../client";
import { ref, watch, watchEffect } from "vue";
import type { SiteEvaluationList } from "../client";
import type { Ref } from "vue";

type SiteEvaluation = SiteEvaluationList["results"][0];

const timemin = ref(Math.floor(new Date(0).valueOf() / 1000));

const evaluations: Ref<SiteEvaluationList | undefined> = ref();
const openedEvaluation: Ref<SiteEvaluation | undefined> = ref();

watchEffect(async () => {
  evaluations.value = await ApiService.getSiteEvaluations();
  timemin.value = evaluations.value.timerange.min;
  state.bbox = evaluations.value.bbox;
});

watch(openedEvaluation, (val) => {
  if (evaluations.value !== undefined) {
    state.bbox = val !== undefined ? val.bbox : evaluations.value.bbox;
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
          />
          <TimeSlider :min="timemin" :max="Math.floor(Date.now() / 1000)" />
          {{ new Date(state.timestamp * 1000).toLocaleString() }}
        </div>
        <EvaluationList
          v-if="evaluations"
          v-model="openedEvaluation"
          :evaluations="evaluations"
        />
      </div>
    </div>
  </div>
</template>
