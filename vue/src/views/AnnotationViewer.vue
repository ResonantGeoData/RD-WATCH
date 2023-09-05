<script setup lang="ts">
import SideBar from "../components/annotationViewer/SideBar.vue"
import SiteDetails from "../components/siteDetails/SiteDetails.vue"
import MapLibre from "../components/MapLibre.vue";
import ModelRunSiteEvalList from "../components/annotationViewer/ModelRunSiteEvalList.vue"
import { ModelRunEvaluationDisplay } from "../components/annotationViewer/ModelRunSiteEvalList.vue"
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

const siteEvalList: Ref<typeof ModelRunSiteEvalList | null> = ref(null)

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
const selectedName: Ref<string | null> = ref(null);
const selectedDateRange: Ref<number[] | null> = ref(null);

const setSelectedEval = (val: ModelRunEvaluationDisplay) => {
  if (val.id !== null) {
    selectedEval.value = val.id
    selectedName.value = val.name
    state.bbox = val.bbox;
    selectedDateRange.value = [val.startDate, val.endDate]
  }
}

watch(selectedModelRun, () => {
    selectedEval.value = null;
    selectedName.value = null;
})

const updateSiteModels = () => {
  if (siteEvalList.value !== null) {
    siteEvalList.value.getSiteEvalIds();
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
    <MapLibre :compact="selectedEval !== null" />
    <SiteDetails
      v-if="selectedEval !== null"
      :site-eval-id="selectedEval"
      :site-evaluation-name="selectedName"
      :date-range="selectedDateRange"
      editable
      style="top:40vh !important; height:60vh"
      @update-list="updateSiteModels()"
    />
  </v-main>
  <ModelRunSiteEvalList
    v-if="selectedModelRun !== null"
    ref="siteEvalList"
    :model-run="selectedModelRun"
    :selected-eval="selectedEval"
    @selected="setSelectedEval($event)"
  />
</template>
