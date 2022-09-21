<script setup lang="ts">
import EvaluationDetail from "./EvaluationDetail.vue";
import type { SiteEvaluationList } from "../client";

type SiteEvaluation = SiteEvaluationList["results"][0];

const props = defineProps<{
  modelValue: undefined | SiteEvaluation;
  evaluations: SiteEvaluationList;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", evaluation: SiteEvaluation | undefined): void;
}>();

function handleToggle(evaluation: SiteEvaluation) {
  if (props.modelValue?.id === evaluation.id) {
    // closed
    emit("update:modelValue", undefined);
  } else {
    // open
    emit("update:modelValue", evaluation);
  }
}
</script>

<template>
  <div class="h-full overflow-y-scroll px-2">
    <EvaluationDetail
      v-for="evaluation in props.evaluations?.results"
      :key="evaluation.id"
      :evaluation="evaluation"
      :open="evaluation.id === props.modelValue?.id"
      class="mt-2"
      @toggle="() => handleToggle(evaluation)"
    />
  </div>
</template>
