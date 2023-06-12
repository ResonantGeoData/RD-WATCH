<script setup lang="ts">
import { computed, onUnmounted, ref } from "vue";
import { EnabledSiteObservations, SiteObservationImage, state } from '../../store'
import EvaluationDisplay from "./EvaluationDisplay.vue";
import SiteEvalSettings from "./SiteEvalSettings.vue";
import { hoveredInfo } from "../../interactions/mouseEvents";


const expandSettings = ref(false);
const clearAll = () => {
  state.enabledSiteObservations = [];
  state.selectedObservations = [];
}
const updateSources = () => {
  const newObservations: EnabledSiteObservations[] = [];
  state.enabledSiteObservations.filter((item) => {
    const tempImages: SiteObservationImage[] = [];
    item.images.forEach((image) => {
      if (!state.siteObsSatSettings.observationSources.includes(image.source)) {
        image.disabled = true;
      } else if (image.disabled) {
        delete image.disabled;
      }
      tempImages.push(image);
    });
    if (tempImages.length) {
      item.images = tempImages;
    }
    newObservations.push(item);
  });
  state.enabledSiteObservations = newObservations;
}
const S2Imagery = computed({
  get() {
    return state.siteObsSatSettings.observationSources.includes('S2');
  },
  set(val: boolean) {
    if (val && !state.siteObsSatSettings.observationSources.includes('S2')) {
      state.siteObsSatSettings.observationSources.push('S2');
    }
    if (!val && state.siteObsSatSettings.observationSources.includes('S2')) {
      const index = state.siteObsSatSettings.observationSources.findIndex((item) => item === 'S2');
      state.siteObsSatSettings.observationSources.splice(index, 1);
    }
    updateSources();
  },
});
const WVImagery = computed({
  get() {
    return state.siteObsSatSettings.observationSources.includes('WV');
  },
  set(val: boolean) {
    if (val && !state.siteObsSatSettings.observationSources.includes('WV')) {
      state.siteObsSatSettings.observationSources.push('WV');
    }
    if (!val && state.siteObsSatSettings.observationSources.includes('WV')) {
      const index = state.siteObsSatSettings.observationSources.findIndex((item) => item === 'WV');
      state.siteObsSatSettings.observationSources.splice(index, 1);
    }
    updateSources();
  },
});

onUnmounted(() => {
  if (state.loopingInterval !== null) {
    clearInterval(state.loopingInterval);
    state.loopingId = null;
  }
})
</script>

<template>
  <v-card
    v-if="state.selectedObservations.length"
    class="pa-5 site-eval-card"
  >
    <v-row>
      <h1 class="mx-4 mt-2">
        Selected Evaluations
      </h1>
    </v-row>
    <v-row>
      <v-checkbox
        v-model="S2Imagery"
        label="S2"
        density="compact"
        class="mx-2"
      />
      <v-checkbox
        v-model="WVImagery"
        label="WV"
        density="compact"
        class="mx-2"
      />



      <v-btn
        size="small"
        @click="clearAll()"
      >
        Clear All
      </v-btn>
      <v-spacer />
      <v-icon
        :color="expandSettings ? 'rgb(37, 99, 235)' : 'black'"
        @click="expandSettings = !expandSettings"
      >
        mdi-cog
      </v-icon>
    </v-row>
    <div class="px-5">
      <site-eval-settings
        v-if="expandSettings"
      />
    </div>
    <div style="overflow-y:auto">
      <evaluation-display
        v-for="item in state.selectedObservations"
        :key="`siteObs_${item.id}`"
        :site-observation="item"
        class="siteObs"
        :class="{ outlined: hoveredInfo.siteId.includes(item.id) }"
      />
    </div>
  </v-card>
</template>

<style scoped>
.sample {
  z-index: 999;
}
.siteObs {
  margin: 10px;
  border: 3px solid transparent;
  max-height: calc(100vh - 10px);

}
.outlined {
  background-color: orange;
  border: 3px solid orange;
}
.checkboxlabel {
  display: inline;
}
.observation-sidebar{
  max-width: 350px;
  min-width: 350px;
}
.hover:hover {
  cursor: pointer;
}

.site-eval-card{
  min-height: 100vh;
}
</style>
