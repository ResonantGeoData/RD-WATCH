<script setup lang="ts">
import { ref, watch } from "vue";

const props = defineProps<{
  modelValue: string[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", mode: string[]): void;
}>();

const modes = ['batch', 'incremental'];
const selectedMode = ref<string[]>(props.modelValue);

watch(() => props.modelValue, () => {
  if (props.modelValue) {
    selectedMode.value = props.modelValue;
  }
});

watch(selectedMode, () => {
  emit('update:modelValue', selectedMode.value);
});
</script>

<template>
  <v-select
    v-model="selectedMode"
    clearable
    multiple
    persistent-clear
    density="compact"
    variant="outlined"
    label="Mode"
    placeholder="Mode"
    :items="modes"
    single-line
    class="dropdown"
  />
</template>

<style scoped>
.dropdown {
  max-width: 180px;
}
</style>
