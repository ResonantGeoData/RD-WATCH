<script setup lang="ts">
import FilterSelect from "../FilterSelect.vue";
import { ref, watch, watchEffect } from "vue";
import { ApiService } from "../../client";
import type { Ref } from "vue";
import type { Performer } from "../../client";

type SelectedPerformer = Performer | null;

const props = defineProps<{
  modelValue: SelectedPerformer;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", performer: SelectedPerformer): void;
}>();

const performers: Ref<Performer[]> = ref([]);
const selectedPerformer: Ref<SelectedPerformer> = ref(props.modelValue);

watchEffect(async () => {
  const performerList = await ApiService.getPerformers();
  const performerResults = performerList.items
  performerResults.sort((a, b) => (a.team_name > b.team_name ? 1 : -1));
  performers.value = performerResults;
});

watch(selectedPerformer, (val) => emit("update:modelValue", val));
</script>

<template>
  <FilterSelect
    v-model="selectedPerformer"
    :label="`Performer (${performers.length})`"
    :options="performers"
    value-key="team_name"
  />
</template>
