<script setup lang="ts">
import { ref, watch } from "vue";
import type { Ref } from "vue";
import type { Region } from "../../client";
import { useRouter, } from 'vue-router';
import { state } from "../../store";

const router = useRouter();


const props = defineProps<{
  modelValue?: Region;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", region?: Region): void;
}>();

const selectedRegion: Ref<string | undefined> = ref(props.modelValue);

watch(() => props.modelValue, () => {
  if (props.modelValue) {
    const found = state.regionList.find((item) => item.value === props.modelValue)
    if (!found) {
      selectedRegion.value = undefined;
      emit("update:modelValue", selectedRegion.value);
    } else {
    selectedRegion.value = props.modelValue;
    }
  }
});

watch(() => state.filters.regions, () => {
  if (!state.filters.regions?.length)  {
    selectedRegion.value = undefined;
    emit("update:modelValue", selectedRegion.value);
  }
})

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
    :label="`Region (${state.regionList.length})`"
    :placeholder="`Region (${state.regionList.length})`"
    :items="state.regionList"
    item-title="name"
    item-value="value"
    single-line
    class="dropdown"
  >
    <template #item="{ props, item }">
      <v-list-item
        v-if="item.raw.ownerUsername !== 'None'"
        v-bind="props"
        :subtitle="item.raw.ownerUsername"
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
