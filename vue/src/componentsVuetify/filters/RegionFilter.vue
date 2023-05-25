<script setup lang="ts">
import FilterSelect from "../FilterSelect.vue";
import { state } from "../../store";
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
  const generatedMap: Record<Region['id'], Region['name']> = {}
    regionResults.forEach((item) => {
      generatedMap[item.id] = item.name;
  })
  state.regionMap = generatedMap;
  
});

watch(selectedRegion, (val) => emit("update:modelValue", val));
</script>

<template>
  <v-select
    v-model="selectedRegion"
    density="compact"
    variant="outlined"
    :label="`Region (${regions.length})`"
    :placeholder="`Region (${regions.length})`"
    :items="regions"
    item-title="name"
    item-value="id"
  />
</template>
