<script setup lang="ts">
import { state } from "../store";

defineProps<{
  min: number;
  max: number;
}>();
</script>

<template>
  <input
    v-model.number="state.timestamp"
    :min="min"
    :max="max"
    :disabled="min == max"
    class="chrome-range w-full"
    type="range"
  />
</template>
