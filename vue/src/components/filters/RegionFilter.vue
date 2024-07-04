<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { ApiService } from "../../client";
import type { Ref } from "vue";
import type { Region } from "../../client";
import { useRouter, } from 'vue-router';
import { RegionDetail } from "../../client/models/Region";
import { state } from "../../store";

const router = useRouter();


const props = defineProps<{
  modelValue?: Region;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", region?: Region): void;
}>();

const regions: Ref<RegionDetail[]> = ref([]);
const selectedRegion: Ref<string | undefined> = ref(props.modelValue);
const loadRegions =  async () => {
  const regionList = await ApiService.getRegionDetails();
  const regionResults = regionList.items;

  const tempRegionMap: Record<string, number> = {};
  regionResults.forEach((item) => tempRegionMap[item.value] = item.id);
  state.regionMap = tempRegionMap;
  regionResults.sort((a, b) => {
    // First sort by whether the owner is not 'None'
    if (a.owner !== 'None' && b.owner === 'None') {
      return -1;
    }
    if (a.owner === 'None' && b.owner !== 'None') {
      return 1;
    }
    // If both have owners or both do not, sort by name
    return a.name.localeCompare(b.name);
  });  
  regions.value = regionResults;
};
onMounted(() => loadRegions());

watch(() => ApiService.getRegionDetails(), loadRegions);

watch(() => props.modelValue, () => {
  if (props.modelValue) {
    selectedRegion.value = props.modelValue;
  }
});
watch(() => props.modelValue, () => {
  selectedRegion.value = props.modelValue;
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
    clearable
    persistent-clear
    :label="`Region (${regions.length})`"
    :placeholder="`Region (${regions.length})`"
    :items="regions"
    item-title="name"
    item-value="value"
    single-line
    class="dropdown"
  >
    <template #item="{ props, item }">
      <v-list-item
        v-if="item.raw.owner !== 'None'"
        v-bind="props"
        :subtitle="item.raw.owner"
      />
      <v-list-item
        v-else
        v-bind="props"
        :title="item.raw.name"
      />
    </template>
  </v-select>
</template>
<style scoped>
.dropdown {
  max-width: 180px;
}
</style>
