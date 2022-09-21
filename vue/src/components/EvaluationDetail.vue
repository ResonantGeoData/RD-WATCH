<script setup lang="ts">
import TimeSlider from "./TimeSlider.vue";
import { ApiService } from "../client";
import { state } from "../store";
import { Ref, computed, ref } from "vue";
import type { SiteEvaluationList, SiteObservationList } from "../client";

type SiteEvaluation = SiteEvaluationList["results"][0];

const props = defineProps<{
  evaluation: SiteEvaluation;
  open: boolean;
}>();

const emit = defineEmits<{
  (e: "toggle"): void;
}>();

const observations: Ref<SiteObservationList | undefined> = ref();
const observation = computed(() =>
  observations.value == undefined
    ? undefined
    : observations.value["results"].find(
        (obs) =>
          obs.timerange.min <= state.timestamp &&
          (obs.timerange.max > state.timestamp ||
            obs.timerange.min == obs.timerange.max)
      )
);

async function handleClick() {
  emit("toggle");
  if (observations.value === undefined) {
    observations.value = await ApiService.getSiteObservations(
      props.evaluation.id.toString()
    );
  }
}
</script>

<template>
  <details
    class="group relative rounded-lg border-2 border-gray-50 open:border-blue-600 hover:border-gray-200 open:hover:border-blue-600"
    :open="props.open"
  >
    <summary
      class="cursor-pointer select-none list-none bg-gray-50 p-2 group-open:bg-blue-600 group-hover:bg-gray-200 group-open:group-hover:bg-blue-600"
      @click.prevent="handleClick"
    >
      <div class="grid grid-cols-2">
        <div
          class="col-span-1 text-left font-mono text-lg font-bold group-open:text-white"
        >
          {{ evaluation.site }}
        </div>
        <div
          class="col-span-1 text-right text-xs font-light text-gray-400 group-open:text-gray-100"
        >
          [site]
        </div>
        <div
          class="col-span-1 text-left text-xs font-light group-open:text-white"
        >
          {{ new Date(evaluation.timestamp * 1000).toLocaleString() }}
        </div>
        <div
          class="col-span-1 text-right text-xs font-light text-gray-400 group-open:text-gray-100"
        >
          [completion]
        </div>
        <div
          class="col-span-2 rounded text-right text-xs text-gray-50 group-open:text-blue-600"
        >
          <div
            class="float-right mt-1 rounded bg-gray-400 pl-1 pr-1 group-open:bg-gray-100"
          >
            {{ evaluation.performer.short_code }}
          </div>
        </div>
      </div>
    </summary>
    <div class="grid grid-cols-4 p-2">
      <div class="col-span-4">
        <TimeSlider
          :min="evaluation.timerange.min"
          :max="evaluation.timerange.max"
        />
      </div>
      <div class="col-span-1 text-left text-sm font-light text-gray-600">
        score:
      </div>
      <div class="col-span-3 text-left font-mono text-sm">
        {{ observation?.score }}
      </div>
      <div class="col-span-1 text-left text-sm font-light text-gray-600">
        label:
      </div>
      <div class="col-span-3 text-left font-mono text-sm">
        {{ observation?.label }}
      </div>
      <div class="col-span-1 text-left text-sm font-light text-gray-600">
        source:
      </div>
      <div class="col-span-3 text-left font-mono text-sm">
        {{ observation?.constellation }}
      </div>
    </div>
  </details>
</template>
