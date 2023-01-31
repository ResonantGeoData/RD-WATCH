<script setup lang="ts">
defineProps<{
  modelValue: boolean;
  label: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", choice: boolean): void;
}>();
</script>

<template>
  <div
    v-if="!modelValue"
    class="h-5 cursor-pointer select-none whitespace-nowrap rounded bg-gray-300 text-sm text-gray-600 hover:bg-gray-400 hover:text-gray-100"
    @click="emit('update:modelValue', true)"
  >
    <span class="mx-2 grow-0 self-center">{{ label }}</span>
  </div>
  <div
    v-if="modelValue"
    class="h-5 cursor-pointer select-none whitespace-nowrap rounded bg-blue-600 text-sm text-gray-100 hover:bg-blue-400"
    @click="emit('update:modelValue', false)"
  >
    <span class="flex items-baseline">
      <span class="ml-1 grow-0 self-center">✓</span>
      <span class="mx-2 grow-0 self-center">{{ label }}</span>
    </span>
  </div>
</template>
