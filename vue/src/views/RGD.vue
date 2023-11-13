<script setup lang="ts">
import SideBar from "../components/SideBar.vue"
import MapLibre from "../components/MapLibre.vue";
import RightBar from "../components/RightBar.vue"
import LayerSelection from "../components/LayerSelection.vue";
import { onMounted } from "vue";
import { state } from "../store";

interface Props {
  region?: string;
  selected?: number[] | string;
}
const props = withDefaults(defineProps<Props>(), {
  region: undefined,
  selected: undefined,
});

onMounted(() => {
  if (props.region) {
    state.filters = {
      ...state.filters,
      regions: [props.region],
    };
  }
});


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
    <layer-selection />
    <MapLibre />
  </v-main>
  <RightBar />
</template>
