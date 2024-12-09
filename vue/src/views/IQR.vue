<script setup lang="ts">
import SideBar from "../components/SideBar.vue";
import MapLibre from "../components/MapLibre.vue";
import LayerSelection from "../components/LayerSelection.vue";
import ImageViewer from "../components/imageViewer/ImageViewer.vue";
import SiteList from "../components/siteList/SiteList.vue";
import MapLegend from "../components/MapLegend.vue";
import { onMounted, provide, watch } from "vue";
import { loadAndToggleSatelliteImages, state, updateRegionList } from "../store";
import AddRegion from "../components/AddRegion.vue";
import { ApiService } from "../client";
import { IQR_KEY, useIQR } from "../use/useIQR";
import IqrSimilarSites from "../components/iqr/IqrSimilarSites.vue";

interface Props {
  region?: string;
  selected?: number[] | string;
}
const props = withDefaults(defineProps<Props>(), {
  region: undefined,
  selected: undefined,
});

onMounted(async () => {
  await updateRegionList();
  if (props.region) {
    state.filters = {
      ...state.filters,
      regions: [props.region],
    };
  }
});

watch(() => ApiService.getApiPrefix(), async () => {
  await updateRegionList();
  if (props.region) {
    state.filters = {
      ...state.filters,
      regions: [props.region],
    };
  }
});

provide(IQR_KEY, true);
const iqr = useIQR();

let lastSelectedSiteId = '';
watch(() => state.selectedImageSite, (site) => {
  if (site?.siteId) {
    lastSelectedSiteId = site.siteId;
  }
});

function onImageViewerClose() {
  if (iqr.getAndUnsetHideMapImageOnImageViewerCloseFlag()) {
    loadAndToggleSatelliteImages(lastSelectedSiteId, false);
  }
}
</script>

<template>
  <v-navigation-drawer
    location="left"
    width="400"
    sticky
    permanent
    class="h-100 overflow-hidden"
  >
    <SideBar />
  </v-navigation-drawer>
  <v-main style="z-index: 1; height: 100%">
    <layer-selection />
    <MapLibre />
    <ImageViewer
      v-if="!!state.selectedImageSite"
      :site-eval-id="state.selectedImageSite.siteId"
      :site-evaluation-name="state.selectedImageSite.siteName"
      :date-range="state.selectedImageSite.dateRange"
      style="position: relative; top: -60vh !important; height: 60vh"
      @close="onImageViewerClose"
    />
  </v-main>
  <span>
    <span>
      <v-navigation-drawer
        v-if="state.filters.configuration_id?.length || state.filters.addingRegionPolygon"
        location="left"
        floating
        width="250"
        sticky
        permanent
        class="fill-height site-list"
        style="overflow-y: hidden"
      >
        <v-row
          dense
          class="pa-0 ma-0"
        >
          <v-col class="navcolumn">
            <SiteList
              v-if="
                state.filters.configuration_id &&
                  !state.filters.addingSitePolygon &&
                  !state.filters.addingRegionPolygon
              "
              :model-runs="state.filters.configuration_id"
              style="flex-grow: 1"
            />
            <add-region v-if="state.filters.addingRegionPolygon" />
          </v-col>
        </v-row>
      </v-navigation-drawer>
      <MapLegend class="static-map-legend" />
      <v-navigation-drawer
        v-if="iqr.state.site"
        location="right"
        floating
        width="250"
        sticky
        permanent
        class="fill-height site-list overflow-y-hidden"
      >
        <iqr-similar-sites :site="iqr.state.site" />
      </v-navigation-drawer>
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

.iqr-candidate {
  border-top: 1px solid rgba(0, 0, 0, 0.5);
}
</style>
