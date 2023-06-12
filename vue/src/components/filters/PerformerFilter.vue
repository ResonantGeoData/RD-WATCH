<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";
import { ApiService, PerformerList } from "../../client";
import type { Ref } from "vue";
import type { Performer } from "../../client";

type SelectedPerformer = Performer | null;

const props = defineProps<{
  modelValue: SelectedPerformer;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", performer: SelectedPerformer): void;
}>();

const performers: Ref<{value: number; title: string}[]> = ref([]);
const selectedPerformer: Ref<number | undefined> = ref(props.modelValue?.id);
const performerList: Ref<PerformerList | null> = ref(null);
watchEffect(async () => {
  performerList.value = await ApiService.getPerformers();
  const performerResults = performerList.value.items
  performerResults.sort((a, b) => (a.team_name > b.team_name ? 1 : -1))
  performers.value = performerResults.map((item) => ({title: item.team_name, value: item.id }));
});

watch(selectedPerformer, (val) => {
  if (performerList.value !== null) {
    const newPerformer = performerList.value.items.find((item) => item.id === val);
    if (newPerformer) {
      emit("update:modelValue", newPerformer);
      return;
    }
  }
  emit("update:modelValue", null);
});
</script>

<template>
  <v-select
    v-model="selectedPerformer"
    clearable
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