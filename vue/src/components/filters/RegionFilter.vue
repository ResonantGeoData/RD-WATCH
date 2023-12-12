<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";
import { ApiService } from "../../client";
import type { Ref } from "vue";
import type { Region } from "../../client";
import { useRouter, } from 'vue-router';

const router = useRouter();


const props = defineProps<{
  modelValue?: Region;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", region?: Region): void;
}>();

const regions: Ref<Region[]> = ref([]);
const selectedRegion: Ref<string | undefined> = ref(props.modelValue);
watchEffect(async () => {
  const regionList = await ApiService.getRegions();
  const regionResults = regionList.items;
  regionResults.sort((a, b) => (a > b ? 1 : -1));
  regions.value = regionResults;
});

watch(() => props.modelValue, () => {
  if (props.modelValue) {
    selectedRegion.value = props.modelValue;
  }
});

watch(selectedRegion, (val) => {
  let prepend = '/'
  if (router.currentRoute.value.fullPath.includes('scoring')) {
    prepend += 'scoring/'
  }
  if (router.currentRoute.value.fullPath.includes('proposals')) {
    prepend += 'proposals/'
  }
  if (val) {
    router.push(`${prepend}${val}`)
    emit("update:modelValue", val);
    return;
  }
  router.push({ path: prepend });
  emit("update:modelValue", undefined);
});
</script>

<template>
  <v-select
    v-model="selectedRegion"
    density="compact"
    variant="outlined"
    :label="`Region (${regions.length})`"
    :placeholder="`Region (${regions.length})`"
    :items="regions"
    single-line
    class="dropdown"
  />
</template>
<style scoped>
.dropdown {
  max-width: 180px;
}
</style>
