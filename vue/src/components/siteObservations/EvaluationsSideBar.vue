<script setup lang="ts">
import { Ref, onUnmounted, ref } from "vue";
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

const baseSources: Ref<('S2' |'WV' | 'L8')[]> = ref(['S2', 'WV', 'L8'])

const sources: Ref<('S2' |'WV' | 'L8')[]> = ref(['S2', 'WV', 'L8']);
const updateSatSources = () => {
  console.log('Updating Sources');
  state.siteObsSatSettings = {...state.siteObsSatSettings, observationSources: sources.value };
  updateSources();
  console.log(state.siteObsSatSettings.observationSources);
};

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
    class="px-5 pb-5 site-eval-card"
  >
    <v-row>
      <h1 class="mx-4 mt-2">
        Selected Evaluations
      </h1>
    </v-row>

    <v-row>
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
    <v-row
      dense
      class="pt-2"
    >
      <v-select
        v-model="sources"
        :items="baseSources"
        label="Sources"
        multiple
        density="compact"
        closable-chips	
        chips
        class="mx-2"
        width="150"
        @update:model-value="updateSatSources()"
      />
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
        :class="{ outlined: hoveredInfo.siteId.includes(item.id), evalhovered: state.filters.hoverSiteId === item.id }"
        @mouseenter="state.filters.hoverSiteId = item.id"
        @mouseleave="state.filters.hoverSiteId = -1"
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
.evalhovered {
  border: 3px solid orange;
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
  overflow-y:auto;
  background-color: white;
}
.eval-controls {
  position:sticky;
  top:0px;
  z-index:2;
  background-color: white;
}
</style>
