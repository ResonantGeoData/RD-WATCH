<script setup lang="ts">
import { computed, onUnmounted, ref } from "vue";
import { EnabledSiteObservations, SiteObservationImage, state } from '../../store'
import EvaluationDisplay from "./EvaluationDisplay.vue";
import SiteEvalSettings from "./SiteEvalSettings.vue";
import { hoveredInfo } from "../../interactions/mouseEvents";
import { Cog6ToothIcon } from "@heroicons/vue/24/solid";


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
  <div
    v-if="state.selectedObservations.length"
    class="fixed h-screen w-200 pt-2 pb-2 pr-2 absolute inset-y-0 right-0 observation-sidebar"
  >
    <div
      class="flex h-full flex-col overflow-hidden rounded-xl bg-white drop-shadow-2xl "
    >
      <h1 class="mx-4">
        Selected Evaluations
      </h1>
      <div class="grid grid-cols-4 mx-4">
        <div class="col-span-1 mt-1">
          <span class="label checkboxlabel">
            <span class="label-text">S2:</span>
            <input
              v-model="S2Imagery"
              type="checkbox"
              class="checkbox-primary checkbox-xs ml-1"
            >
          </span>
        </div>

        <div class="col-span-1 mt-1">
          <span class="label checkboxlabel">
            <span class="label-text">WV:</span>
            <input
              v-model="WVImagery"
              type="checkbox"
              class="checkbox-primary checkbox-xs ml-1"
            >
          </span>
        </div>

        <div class="col-span-1">
          <button
            class="btn-xs btn-error"
            @click="clearAll()"
          >
            Clear All
          </button>
        </div>
        <div class="col-span-1 justify-self-end">
          <Cog6ToothIcon
            class="icon h-5 text-blue-600 hover"
            data-tip="Settings"
            @click="expandSettings = !expandSettings"
          />
        </div>
      </div>
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
    </div>
  </div>
</template>

<style scoped>
.sample {
  z-index: 999;
}
.siteObs {
  margin: 10px;
  border: 5px solid transparent;

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

</style>
