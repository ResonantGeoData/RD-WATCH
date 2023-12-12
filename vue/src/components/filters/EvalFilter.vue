<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";
import { ApiService, EvalList } from "../../client";
import type { Ref } from "vue";
import type { Eval } from "../../client";
import { state } from "../../store";

const props = defineProps<{
  modelValue: Eval[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", eval?: Eval[]): void;
}>();

const evals: Ref<Eval[]> = ref([]);
const selectedEvals: Ref<Eval[]> = ref(props.modelValue);
watchEffect(async () => {
  const evalList = await ApiService.getEvals();
  const evalResults = evalList.items
  evals.value = evalResults;
});

watch(() => props.modelValue, () => {
  if (props.modelValue) {
    selectedEvals.value = props.modelValue;
  }
});

watch(selectedEvals, (l) => {
  if (l) {
    emit("update:modelValue", l);
    return;
  }
  emit("update:modelValue", []);
});
</script>

<template>
  <v-select
    v-model="selectedEvals"
    clearable
    persistent-clear
    multiple
    density="compact"
    variant="outlined"
    :label="`Evaluation (${evals.length})`"
    :placeholder="`Evaluation (${evals.length})`"
    :items="evals"
    single-line
    class="dropdown"
  />
</template>
<style scoped>
.dropdown {
  max-width: 180px;
}
</style>
