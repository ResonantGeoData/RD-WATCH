<script setup lang="ts">
import ModelRunDetail from "./ModelRunDetail.vue";
import type { ModelRun, QueryArguments } from "../client";
import { ref, watchEffect } from "vue";
import type { Ref } from "vue";
import { ApiService } from "../client";
import { state } from "../store";
import { LngLatBounds } from "maplibre-gl";

interface KeyedModelRun extends ModelRun {
  key: string;
}

const props = defineProps<{
  filters: QueryArguments;
}>();

const emit = defineEmits<{
  (e: "update:timerange", timerange: ModelRun["timerange"]): void;
}>();

const modelRuns: Ref<KeyedModelRun[]> = ref([]);
const openedModelRuns: Ref<Set<KeyedModelRun["key"]>> = ref(new Set());
const resultsBoundingBox = ref({
  xmin: -180,
  ymin: -90,
  xmax: 180,
  ymax: 90,
});

watchEffect(async () => {
  const modelRunList = await ApiService.getModelRuns({
    limit: 0,
    ...props.filters,
  });
  const modelRunResults = modelRunList.results;
  const keyedModelRunResults = modelRunResults.map((val) => {
    return { ...val, key: `${val.id}|${val.region.id}` };
  });

  const bounds = new LngLatBounds();
  modelRunList.bbox.coordinates
    .flat()
    .forEach((c) => bounds.extend(c as [number, number]));
  const bbox = {
    xmin: bounds.getWest(),
    ymin: bounds.getSouth(),
    xmax: bounds.getEast(),
    ymax: bounds.getNorth(),
  };
  resultsBoundingBox.value = bbox;
  state.bbox = bbox;
  modelRuns.value = keyedModelRunResults;
  emit("update:timerange", modelRunList["timerange"]);
});

function handleToggle(modelRun: KeyedModelRun) {
  if (openedModelRuns.value.has(modelRun.key)) {
    openedModelRuns.value.delete(modelRun.key);
  } else {
    openedModelRuns.value.add(modelRun.key);
  }

  if (openedModelRuns.value.size > 0) {
    const bounds = new LngLatBounds();
    modelRuns.value
      .filter((modelRun) => openedModelRuns.value.has(modelRun.key))
      .forEach((modelRun) =>
        modelRun.bbox?.coordinates
          .flat()
          .forEach((c) => bounds.extend(c as [number, number]))
      );
    state.bbox = {
      xmin: bounds.getWest(),
      ymin: bounds.getSouth(),
      xmax: bounds.getEast(),
      ymax: bounds.getNorth(),
    };

    const configurationIds: Set<number> = new Set();
    modelRuns.value
      .filter((modelRun) => openedModelRuns.value.has(modelRun.key))
      .map((modelRun) => configurationIds.add(modelRun.id));
    state.filters = {
      ...state.filters,
      configuration_id: Array.from(configurationIds),
    };
    console.log(state.filters);
  } else {
    state.bbox = resultsBoundingBox.value;
    state.filters = {
      ...state.filters,
      configuration_id: undefined,
    };
  }
}
</script>

<template>
  <div class="h-4/5 overflow-y-scroll px-2">
    <ModelRunDetail
      v-for="modelRun in modelRuns"
      :key="modelRun.key"
      :model-run="modelRun"
      :open="openedModelRuns.has(modelRun.key)"
      class="mt-2"
      @toggle="() => handleToggle(modelRun)"
    />
  </div>
</template>
