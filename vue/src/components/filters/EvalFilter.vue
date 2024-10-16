<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { ApiService } from "../../client";
import type { Ref } from "vue";
import type { Eval } from "../../client";

const props = defineProps<{
  modelValue: Eval[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", evaluation?: Eval[]): void;
}>();

const evals: Ref<Eval[]> = ref([]);
const selectedEvals: Ref<Eval[]> = ref(props.modelValue);
const loadEvals = async () => {
  if (ApiService.isScoring()) {
    const evalList = await ApiService.getEvals();
    const evalResults = evalList.items
    evals.value = evalResults;
  }
};

watch(() => ApiService.getApiPrefix(), loadEvals);

onMounted(() => loadEvals());

watch(() => props.modelValue, () => {
  if (props.modelValue) {
    selectedEvals.value = props.modelValue;
  }
});

watch(selectedEvals, (evals) => {
  if (evals) {
    emit("update:modelValue", evals);
    return;
  }
  emit("update:modelValue", []);
});
</script>

<template>
  <v-select
    v-model="selectedEvals"
    clearable
    multiple
    persistent-clear
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
