<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ApiService } from "../../client";
import type { ComputedRef, Ref } from "vue";
import type { Performer } from "../../client";
import { state, updatePerformers } from "../../store";

type SelectedPerformers = Performer[];

const props = defineProps<{
  modelValue: SelectedPerformers;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", performer: SelectedPerformers): void;
}>();

const performers: ComputedRef<{value: number; title: string}[]> = computed(() => {
  return state.performerIds.map((id) => {
    const item = state.performerMapping[id];
    return {
      title: item.team_name,
      value: item.id,
    };
  });
});
const selectedPerformers: Ref<number[]> = ref(props.modelValue.map((item) => item.id));

onMounted(() => updatePerformers());

watch(() => ApiService.getPerformers(), updatePerformers);
watch(() => props.modelValue, () => {
  selectedPerformers.value = props.modelValue.map((item) => item.id);
});


// eslint-disable-next-line @typescript-eslint/no-explicit-any
const updateSelected =  (data: readonly any[]) => {
  if (selectedPerformers.value !== null) {
    const newPerformers = data.map((item) => state.performerMapping[item]);
    if (newPerformers.length) {
      emit("update:modelValue", newPerformers);
      return;
    }
  }
  emit("update:modelValue", []);
};
</script>

<template>
  <v-select
    :value="selectedPerformers"
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
    @update:model-value="updateSelected($event)"
  />
</template>

<style scoped>
.dropdown {
  max-width:180px;
}
</style>