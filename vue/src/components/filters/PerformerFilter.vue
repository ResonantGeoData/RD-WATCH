<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";
import { ApiService, PerformerList } from "../../client";
import type { Ref } from "vue";
import type { Performer } from "../../client";
import { state } from "../../store";

type SelectedPerformers = Performer[];

const props = defineProps<{
  modelValue: SelectedPerformers;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", performer: SelectedPerformers): void;
}>();

const performers: Ref<{value: number; title: string}[]> = ref([]);
const selectedPerformers: Ref<number[]> = ref(props.modelValue.map((item) => item.id));
const performerList: Ref<PerformerList | null> = ref(null);
const performerIdMap: Record<number, Performer> = {}
watchEffect(async () => {
  performerList.value = await ApiService.getPerformers();
  const performerResults = performerList.value.items
  performerResults.sort((a, b) => (a.team_name > b.team_name ? 1 : -1))
  performers.value = [];
  performerResults.forEach((item) => {
    performerIdMap[item.id] = item;
    performers.value.push({title: item.team_name, value: item.id });
  })
  state.performerMapping = performerIdMap;
});

watch(() => props.modelValue, () => {
  selectedPerformers.value = props.modelValue.map((item) => item.id);
});


watch(selectedPerformers, () => {
  if (performerList.value !== null) {
    const newPerformers = selectedPerformers.value.map((item) => performerIdMap[item])
    if (newPerformers.length) {
      emit("update:modelValue", newPerformers);
      return;
    }
  }
  emit("update:modelValue", []);
});
</script>

<template>
  <v-select
    v-model="selectedPerformers"
    clearable
    multiple
    persistent-clear
    density="compact"
    variant="outlined"
    :label="`Performer (${performers.length})`"
    :placeholder="`Performer (${performers.length})`"
    :items="performers"
    single-line
    class="dropdown"
  />
</template>

<style scoped>
.dropdown {
  max-width:180px;
}
</style>