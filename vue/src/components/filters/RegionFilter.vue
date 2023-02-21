<script setup lang="ts">
import FilterSelect from "../FilterSelect.vue";
import { ref, watch, watchEffect } from "vue";
import { ApiService } from "../../client";
import type { Ref } from "vue";
import type { Region } from "../../client";

type SelectedRegion = Region | null;

const props = defineProps<{
  modelValue: SelectedRegion;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", region: SelectedRegion): void;
}>();

const regions: Ref<Region[]> = ref([]);
const selectedRegion: Ref<SelectedRegion> = ref(props.modelValue);

watchEffect(async () => {
  const regionList = await ApiService.getRegions();
  const regionResults = regionList["results"];
  regionResults.sort((a, b) => (a.name > b.name ? 1 : -1));
  regions.value = regionResults;
});

watch(selectedRegion, (val) => emit("update:modelValue", val));
</script>

<template>
  <FilterSelect
    v-model="selectedRegion"
    :label="`Region (${regions.length})`"
    :options="regions"
    value-key="name"
  />
</template>
