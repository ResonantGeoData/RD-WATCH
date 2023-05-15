<script setup lang="ts">

import { state } from '../../store'
import { computed } from "vue";

const cloudFilter = computed({
    get() {
      return state.siteObsSatSettings.cloudCoverFilter;
    },
    set(val: number) {
      state.siteObsSatSettings = { ...state.siteObsSatSettings, cloudCoverFilter: val };
    },
  });
  
  const percentBlackFilter = computed({
    get() {
      return state.siteObsSatSettings.percentBlackFilter;
    },
    set(val: number) {
      state.siteObsSatSettings = { ...state.siteObsSatSettings, percentBlackFilter: val };
    },
  });
  
  const imageOpacity = computed({
    get() {
      return state.siteObsSatSettings.imageOpacity;
    },
    set(val: number) {
      state.siteObsSatSettings = { ...state.siteObsSatSettings, imageOpacity: val };
    },
  });
  
</script>

<template>
  <div class="col-span-4">
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Cloud Cover:</span>
        <input
          v-model.number="cloudFilter"
          type="range"
          min="0"
          max="100"
          step="1"
          class="range range-primary"
        >
        <span class="pl-2">
          {{ cloudFilter }}%
        </span>

      </label>
    </div>
  </div>
  <div class="col-span-4">
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Percent Black:</span>
        <input
          v-model.number="percentBlackFilter"
          type="range"
          min="0"
          max="100"
          step="1"
          class="range range-primary"
        >
        <span class="pl-2">
          {{ percentBlackFilter }}%
        </span>

      </label>
    </div>
  </div>
  <div class="col-span-4">
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Image Opacity:</span>
        <input
          v-model.number="imageOpacity"
          type="range"
          min="0"
          max="1"
          step=".05"
          class="range range-primary"
        >
        <span class="pl-2">
          {{ imageOpacity*100 }}%
        </span>
      </label>
    </div>
  </div>
</template>