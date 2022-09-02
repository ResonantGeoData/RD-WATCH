<script setup lang="ts">
import { ApiService } from "../client";
import { ref, watchEffect } from "vue";
import type { SiteEvaluation } from "../client";
import type { Ref } from "vue";

const evaluations: Ref<Array<SiteEvaluation>> = ref([]);

watchEffect(async () => {
  evaluations.value = await ApiService.getSiteEvaluations();
});
</script>

<template>
  <div class="divide-y">
    <div v-for="evaluation in evaluations" :key="evaluation.id">
      <button
        class="relative mb-4 mt-4 h-36 w-full rounded-md hover:bg-slate-50"
      >
        <div class="h-30 absolute left-2 top-2 w-16">
          {{ evaluation.timestamp }}
        </div>
        <div class="h-30 absolute bottom-0 right-0 w-36 text-sm">
          {{ evaluation.performer.short_code }}
        </div>
      </button>
    </div>
  </div>
</template>
