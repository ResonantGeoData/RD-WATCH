<script setup lang="ts">
import SideBar from "../components/annotationViewer/SideBar.vue"
import ImageViewer from "../components/imageViewer/ImageViewer.vue"
import MapLibre from "../components/MapLibre.vue";
import ModelRunSiteEvalList from "../components/annotationViewer/ModelRunSiteEvalList.vue"
import { computed, ref, watch } from "vue";
import { state } from "../store";


const selectedModelRun = computed(() => {
    if (state.filters.configuration_id?.length) {
        return state.filters.configuration_id[0];
    }
    return null;
});

const selectedEval = ref(null);

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
    <div v-if="selectedEval === null">
      Select a SiteId to display the images
    </div>
    <ImageViewer
      v-else
      :site-eval-id="selectedEval"
    />
    <MapLibre compact />
  </v-main>
  <ModelRunSiteEvalList
    v-if="selectedModelRun !== null"
    :model-run="selectedModelRun"
    :selected-eval="selectedEval"
    @selected="selectedEval = $event"
  />
</template>
