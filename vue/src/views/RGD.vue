<script setup lang="ts">
import SideBar from "../components/SideBar.vue"
import MapLibre from "../components/MapLibre.vue";
import LayerSelection from "../components/LayerSelection.vue";
import ImageViewer from "../components/imageViewer/ImageViewer.vue";
import SiteList from "../components/siteList/SiteList.vue";
import MapLegend from "../components/MapLegend.vue";
import { onMounted } from "vue";
import { state } from "../store";
import { ApiService } from "../client";
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
    <ImageViewer
      v-if="!!state.selectedImageSite"
      :site-eval-id="state.selectedImageSite.siteId"
      :site-evaluation-name="state.selectedImageSite.siteName"
      :date-range="state.selectedImageSite.dateRange"
      style="top:40vh !important; height:60vh"
    />
  </v-main>
  <span>
    <span>
      <v-navigation-drawer
        v-if="state.filters.configuration_id?.length && ApiService.getApiPrefix() !== '/api/scoring'"
        location="left"
        floating
        width="250"
        sticky
        permanent
        class="fill-height site-list"
        style="overflow-y: hidden;"
      >
        <v-row
          dense
          class="pa-0 ma-0"
        >
          <v-col
            class="navcolumn"
          >
            <SiteList
              v-if="state.filters.configuration_id"
              :model-runs="state.filters.configuration_id"
              style="flex-grow: 1;"
            />          
          </v-col>
        </v-row>
      </v-navigation-drawer>
      <MapLegend
        class="static-map-legend"
      />
    </span>
  </span>
</template>

<style scoped>
.static-map-legend {
    position: absolute;
    top: 0px;
    right: 0px;
    z-index: 2;
}
.navcolumn {
    display: flex;
    flex-flow: column;
    height: 100vh;
}

</style>