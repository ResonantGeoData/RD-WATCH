<script setup lang="ts">
import SideBar from "../components/annotationViewer/SideBar.vue"
import ImageViewer from "../components/imageViewer/ImageViewer.vue"
import MapLibre from "../components/MapLibre.vue";
import LayerSelection from "../components/LayerSelection.vue";
import AnnotationList from "../components/annotationViewer/AnnotationList.vue"
import AddProposal from "../components/annotationViewer/AddProposal.vue"
import AddRegion from "../components/AddRegion.vue"
import MapLegend from "../components/MapLegend.vue";
import { Ref, computed, onMounted, ref, watch } from "vue";
import { state } from "../store";

interface Props {
  region?: string;
  selected?: number[] | string;
}
const props = withDefaults(defineProps<Props>(), {
  region: undefined,
  selected:undefined,
});

const siteList: Ref<typeof AnnotationList | null> = ref(null)

const selectedModelRun = computed(() => {
    if (state.filters.configuration_id?.length) {
        return state.filters.configuration_id[0];
    }
    return null;
});

onMounted(() => {
  if (props.region) {
    state.filters = { 
      ...state.filters,
      regions: [props.region],
    };
  }
});


watch(selectedModelRun, () => {
  state.selectedImageSite = undefined
})

const updateSiteList = async () => {
  if (siteList.value !== null) {
    // Store the bbox for the sites
    await siteList.value.getSiteProposals();
  }
}
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
    <MapLibre :compact="!!state.selectedImageSite" />
    <ImageViewer
      v-if="!!state.selectedImageSite"
      :site-eval-id="state.selectedImageSite.siteId"
      :site-evaluation-name="state.selectedImageSite.siteName"
      :date-range="state.selectedImageSite.dateRange"
      editable
      style="top:40vh !important; height:60vh"
      @update-list="updateSiteList()"
    />
  </v-main>
  <span>
    <v-navigation-drawer
      v-if="selectedModelRun !== null "
      location="left"
      floating
      width="250"
      sticky
      permanent
      class="fill-height site-list"
      style="overflow-y: hidden;"
    >
      <v-row dense>
        <v-col
          class="navcolumn"
        >
          <annotation-list
            v-if="selectedModelRun !== null && !state.filters.addingSitePolygon && !state.filters.addingRegionPolygon"
            ref="siteList"
            :model-run="selectedModelRun"
            :selected-eval="state.selectedImageSite?.siteId || null"
            style="flex-grow: 1;"
          />
          <add-proposal
            v-if="state.filters.addingSitePolygon"
            :region="region"
          />
          <add-region
            v-if="state.filters.addingRegionPolygon"
          />
        </v-col>
      </v-row>
    </v-navigation-drawer>
    <MapLegend
      class="static-map-legend"
    />
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