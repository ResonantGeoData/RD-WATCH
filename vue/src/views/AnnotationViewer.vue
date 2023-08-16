<script setup lang="ts">
import SideBar from "../components/annotationViewer/SideBar.vue"
import ImageViewer from "../components/imageViewer/ImageViewer.vue"
import MapLibre from "../components/MapLibre.vue";
import ModelRunSiteEvalList from "../components/annotationViewer/ModelRunSiteEvalList.vue"
import { Ref, computed, ref, watch } from "vue";
import { state } from "../store";

interface Props {
  region?: number | string;
  selected?: number[] | string;
}
const props = withDefaults(defineProps<Props>(), {
  region: undefined,
  selected:undefined,
});


const selectedModelRun = computed(() => {
    if (state.filters.configuration_id?.length) {
        return state.filters.configuration_id[0];
    }
    return null;
});

watch(() => state.regionMap, () => {
  if (state.regionMap && props.region) {
    const found = Object.entries(state.regionMap).find(([, key]) => key === props.region);
    if (found) {
      state.filters = {
    ...state.filters,
    region_id: [parseInt(found[0], 10)],
    scoringColoring: null,
  };
    }
  }
})

const selectedEval: Ref<number | null> = ref(null);

const setSelectedEval = ({id, bbox}: {id: number, bbox: { xmin: number; ymin: number; xmax: number; ymax: number }}) => {
  if (id !== null) {
    selectedEval.value = id;
    state.bbox = bbox;
  }
}

watch(selectedModelRun, () => {
    selectedEval.value = null;
})
</script>

<template>
  <v-navigation-drawer
    location="left"
    width="400"
    sticky
    style="max-height:100vh;"
    permanent
  >
    <SideBar />
  </v-navigation-drawer>
  <v-main style="z-index:1">
    <MapLibre :compact="selectedEval !== null" />
    <ImageViewer
      v-if="selectedEval !== null"
      :site-eval-id="selectedEval"
      style="top:40vh !important; height:60vh"
    />
  </v-main>
  <ModelRunSiteEvalList
    v-if="selectedModelRun !== null"
    :model-run="selectedModelRun"
    :selected-eval="selectedEval"
    @selected="setSelectedEval($event)"
  />
</template>
