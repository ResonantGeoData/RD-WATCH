<script setup lang="ts">
import { computed, onUnmounted } from "vue";
import { EnabledSiteObservations, SiteObservationImage, state } from '../../store'
import SiteObservationDisplay from "./SiteObservationDisplay.vue";
import { hoveredInfo } from "../../interactions/popup";
const clearAll = () => {
  state.enabledSiteObservations = [];
  state.selectedObservations = [];
}
const updateSources = () => {
  const newObservations: EnabledSiteObservations[] = [];
  state.enabledSiteObservations.filter((item) => {
    const tempImages: SiteObservationImage[] = [];
    item.images.forEach((image) => {
      if (!state.observationSources.includes(image.type)) {
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
    return state.observationSources.includes('S2');
  },
  set(val: boolean) {
    if (val && !state.observationSources.includes('S2')) {
      state.observationSources.push('S2');
    }
    if (!val && state.observationSources.includes('S2')) {
      const index = state.observationSources.findIndex((item) => item === 'S2');
      state.observationSources.splice(index, 1);
    }
    updateSources();
  },
});
const WVImagery = computed({
  get() {
    return state.observationSources.includes('WV');
  },
  set(val: boolean) {
    if (val && !state.observationSources.includes('WV')) {
      state.observationSources.push('WV');
    }
    if (!val && state.observationSources.includes('WV')) {
      const index = state.observationSources.findIndex((item) => item === 'WV');
      state.observationSources.splice(index, 1);
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
        Selected Observations
      </h1>
      <div class="grid grid-cols-4 mx-4">
        <div class="col-span-4">
          <span class="label checkboxlabel">
            <span class="label-text">S2:</span>
            <input
              v-model="S2Imagery"
              type="checkbox"
              class="checkbox-primary checkbox-xs ml-1"
            >
          </span>

          <span class="label checkboxlabel">
            <span class="label-text">WV:</span>
            <input
              v-model="WVImagery"
              type="checkbox"
              class="checkbox-primary checkbox-xs ml-1"
            >
          </span>

          <button
            class=" btn-xs btn-error"
            @click="clearAll()"
          >
            Clear All
          </button>
        </div>
      </div>

      <site-observation-display
        v-for="item in state.selectedObservations"
        :key="`siteObs_${item.id}`"
        :site-observation="item"
        class="siteObs"
        :class="{ outlined: hoveredInfo.siteId.includes(item.id) }"
      />
    </div>
  </div>
</template>

<style scoped>
.sample {
  z-index: 999;
}
.siteObs {
  margin: 10px;
}
.outlined {
  background-color: orange;
  border: 2px solid orange;
}
.checkboxlabel {
  display: inline;
}
.observation-sidebar{
  max-width: 350px;
}
</style>
