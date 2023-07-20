<script setup lang="ts">
import { state } from "../../store";
import { ref, watch, watchEffect } from "vue";
import { ApiService } from "../../client";
import type { Ref } from "vue";
import type { Region } from "../../client";
import { useRouter,  } from 'vue-router';

const router = useRouter();


const props = defineProps<{
  modelValue?: Region;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", region?: Region): void;
}>();

const regions: Ref<Region[]> = ref([]);
const selectedRegion: Ref<number | undefined> = ref(props.modelValue?.id);
const regionItems: Ref<{title: string; value: number}[]> = ref([]);
watchEffect(async () => {
  const regionList = await ApiService.getRegions();
  const regionResults = regionList.items;
  regionResults.sort((a, b) => (a.name > b.name ? 1 : -1));
  regions.value = regionResults;
  regionItems.value = regionResults.map((item) => ({title: item.name, value: item.id}));
  const generatedMap: Record<Region['id'], Region['name']> = {}
    regionResults.forEach((item) => {
      generatedMap[item.id] = item.name;
  })
  state.regionMap = generatedMap;
});

watch(() => props.modelValue, () => {
  if (props.modelValue) {
    selectedRegion.value = props.modelValue.id;
  }
});

watch(selectedRegion, (val) => {
  let prepend = '/'
  if (router.currentRoute.value.fullPath.includes('annotation')) {
    prepend='/annotation/'
  }
  if (val !== undefined) {
    const found = regions.value.find((item) => item.id === val);

    if (found) {
      router.push(`${prepend}${found.name}`)
      emit("update:modelValue", found);
      return;
    }
  }
  router.push({path: prepend});
  emit("update:modelValue", undefined);
});
</script>

<template>
  <v-select
    v-model="selectedRegion"
    clearable
    persistent-clear
    density="compact"
    variant="outlined"
    :label="`Region (${regions.length})`"
    :placeholder="`Region (${regions.length})`"
    :items="regionItems"
    single-line
    class="dropdown"
  />
</template>
<style scoped>
.dropdown {
  max-width:180px;
}
</style>