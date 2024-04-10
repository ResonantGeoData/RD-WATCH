<script setup lang="ts">
import SideBar from "../components/SideBar.vue"
import MapLibre from "../components/MapLibre.vue";
import RightBar from "../components/RightBar.vue"
import LayerSelection from "../components/LayerSelection.vue";
import { onMounted } from "vue";
import { state } from "../store";
import SiteEvalList from "../components/siteEvalList/SiteEvalList.vue";
import MapLegend from "../components/MapLegend.vue";
import { Ref } from "vue";
import { ref } from "vue";
import { SiteDisplay } from "../components/siteList/SiteListCard.vue";
import { ApiService } from "../client";
interface Props {
  region?: string;
  selected?: number[] | string;
}
const props = withDefaults(defineProps<Props>(), {
  region: undefined,
  selected: undefined,
});

const selectedEval: Ref<string | null> = ref(null);
const selectedName: Ref<string | null> = ref(null);
const selectedDateRange: Ref<number[] | null> = ref(null);
const regionBBox: Ref<SiteDisplay['bbox'] | null> = ref(null);
const setSelectedEval = (val: SiteDisplay | null) => {
  
  if (val && val.id !== null) {
    if (selectedEval.value === null) { // set region bbox if previous val was null
      regionBBox.value = state.bbox;
    }
    selectedEval.value = val.id
    selectedName.value = val.name
    state.bbox = val.bbox;
    selectedDateRange.value = [val.startDate, val.endDate]
  } else {
    selectedEval.value = null;
    selectedName.value = null;
    selectedDateRange.value = null;
    if (regionBBox.value) {
      state.bbox = regionBBox.value;
    }
  }
}

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
        <v-row dense>
          <v-col
            class="navcolumn"
          >
            <SiteEvalList
              v-if="state.filters.configuration_id"
              :model-runs="state.filters.configuration_id"
              :selected-eval="selectedEval"
              style="flex-grow: 1;"
              @selected="setSelectedEval($event)"
            />          
          </v-col>
        </v-row>
      </v-navigation-drawer>
      <MapLegend
        class="static-map-legend"
      />
    </span>
  </span>
  <RightBar />
</template>

<style scoped>
.static-map-legend {
    position: absolute;
    top: 0px;
    right: 0px;
    z-index: 2;
}
</style>