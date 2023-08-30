<script setup lang="ts">
import SideBar from "../components/SideBar.vue"
import MapLibre from "../components/MapLibre.vue";
import RightBar from "../components/RightBar.vue"
import ImageViewer from "../components/imageViewer/ImageViewer.vue"
import { watch } from "vue";
import { state } from "../store";

interface Props {
  region?: number | string;
  selected?: number[] | string;
}
const props = withDefaults(defineProps<Props>(), {
  region: undefined,
  selected:undefined,
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
    <MapLibre :compact="state.openSiteDetails && !!state.selectedSiteDetails && !!state.selectedObservations.length" />
    <ImageViewer
      v-if="state.openSiteDetails && state.selectedSiteDetails && !!state.selectedObservations.length"
      :site-eval-id=" state.selectedSiteDetails.id"
      :site-evaluation-name="state.selectedSiteDetails.name"
      :date-range="state.selectedSiteDetails.dateRange"
    />
  </v-main>
  <RightBar />
</template>
