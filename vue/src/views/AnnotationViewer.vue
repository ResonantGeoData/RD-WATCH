<script setup lang="ts">
import SideBar from "../components/annotationViewer/SideBar.vue"
import ImageViewer from "../components/imageViewer/ImageViewer.vue"
import MapLibre from "../components/MapLibre.vue";
import LayerSelection from "../components/LayerSelection.vue";
import ModelRunSiteEvalList from "../components/annotationViewer/ModelRunSiteEvalList.vue"
import { ModelRunEvaluationDisplay } from "../components/annotationViewer/ModelRunSiteEvalList.vue"
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

const siteEvalList: Ref<typeof ModelRunSiteEvalList | null> = ref(null)

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

const selectedEval: Ref<string | null> = ref(null);
const selectedName: Ref<string | null> = ref(null);
const selectedDateRange: Ref<number[] | null> = ref(null);
const regionBBox: Ref<ModelRunEvaluationDisplay['bbox'] | null> = ref(null);
const setSelectedEval = (val: ModelRunEvaluationDisplay | null) => {
  
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
    <layer-selection />
    <MapLibre :compact="selectedEval !== null" />
    <ImageViewer
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
